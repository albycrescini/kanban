import json, os, io, base64
from flask import Flask, Response, render_template, url_for, request, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from PIL import Image

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, "img")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
db = SQLAlchemy(app)

class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    author = db.Column(db.String(200)) 
    content = db.Column(db.String(200)) # if the tile is an image, the value is the docupath
    media_type = db.Column(db.Integer) # can be 0 if it is text, 1 if it is an image.
    category = db.Column(db.Integer) # can be 0 if organizative, 1 if informative.
    board = db.Column(db.String(200)) # number of the board where the tile needs to be displayed 

    def __repr__(self):
        return "Tile: %r" % self.id

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.Integer) # 0 if running, 1 if complete.

    def __repr__(self):
        return "Board: %r" % self.id

def tiles_map():
    tiles = Tile.query.order_by('id').all()
    dictionary = {}
    for t in tiles:
        dictionary[t.board] = set()
    for t in tiles:
        dictionary[t.board].add(t)

    return dictionary

def alchemy_dict(tile):
    dictionary = {
        "id": str(tile.id),
        "title": str(tile.title),
        "author": str(tile.author),
        "content": str(tile.content),
        "media_type": int(tile.media_type),
        "category": int(tile.category),
        "board": str(tile.board)
    }
    return (dictionary)

def alchemy_board(board):
    dictionary = {
        "id": str(board.id),
        "title": str(board.title),
        "status": str(board.status)
    }
    return (dictionary)

@app.route('/')
def index():
    dictionary = tiles_map()
    return render_template('index.html')

@app.route('/add_board', methods=['GET', 'POST'])
def add_board():
    if(request.method == 'POST'):
        title = request.form['title']
        status = 1 # imposta stato attivo

        if(title == "" or None):
            return Response("Ricontrolla i campi inseriti.", status=403)
        try:
            if(Board.query.filter_by(title=title).first() == None):
                db.session.add(Board(title=title, status=status))
                db.session.commit()
            else:
                return Response("La colonna esiste già tra le attive o le archiviate. Per favore, usa un nome differente.", status=403)
        except Exception as e:
            return("Error", e)
        return render_template("index.html")
    elif(request.method == 'GET'):
        return render_template('add_board.html')

@app.route('/add_tile', methods=['GET', 'POST'])
def add_tile():
    if(request.method == 'POST'):
        print(request.form)
        title = request.form['title']
        author = request.form['author']
        board = request.form['board']

        if(Board.query.filter_by(title=board).first() == None):
            return Response("La colonna indicata non esiste. Per favore, scegline un'altra.", status=403)
        
        content = ""
        file = ""
        category = 0
        media_type = 0
        
        try:
            if (request.form['media_type'] == "on" or request.form['media_type'] == 1): # se è una immagine
                media_type = 1
                file = request.files['img']
                image = Image.open(file)
                image_io = io.BytesIO()
                image.thumbnail((900, 900))
                image.save(image_io, 'png')
                content = str(base64.b64encode(image_io.getvalue()))[2:-1]
        except KeyError as e:
            media_type = 0
            content = request.form['tile_content']
            pass
        except Exception as e:
            print(e)
            return Response("Error media_type", status=403)

        try:
            if (request.form['category'] == "on" or request.form['category'] == 1): # se è di tipo organizzativo
                category = 1
        except KeyError as e:
            category = 0
            pass

        except:
            return Response("Error category", status=403)

        new_tile = Tile(title=title, author=author, content=content, category=category, media_type=media_type, board=board)

        if((title == "" or None) or (author == "" or None)
            or (content == "" or None) or (category == "" or None) 
            or (media_type == "" or None) or (board == "" or None)):
            return Response("Ricontrolla i campi inseriti.", status=403)
    
        try:
            db.session.add(new_tile)
            db.session.commit()
            # return Response("Inserimento avvenuto con successo", status=200)
        except Exception as e:
            return Response("Error db-insert", status=403)
        return render_template('index.html')    
    elif(request.method == 'GET'):
        return render_template('add_tile.html')

@app.route('/edit_tile', methods=['GET', 'POST'])
def edit_tile():
    if(request.method == 'POST'):
        title = request.form['title']
        author = request.form['author']
        board = request.form['board']
        media_type = 0
        id = request.form['id']

        try:
            content = request.form['tile_content']
        except KeyError:
            content = None
            pass
        except Exception as e:
            return Response("Error" + str(e), status=403)

        try:
            if (request.form['media_type'] == "on" or request.form['media_type'] == '1'): # se è una immagine
                media_type = 1
        except KeyError:
            media_type = 0
            pass
        except Exception as e:
            return Response("Error" + str(e), status=403)

        try:
            if (request.form['category'] == "on"): # se è di tipo organizzativo
                category = 1 
        except KeyError:
            category = 0
            pass
        except Exception as e:
            return Response("Error" + str(e), status=403)

        if((title == "" or None) or (author == "" or None)
            or (content == "" or None) or (category == "" or None) 
            or (media_type == "" or None) or (board == "" or None)):
            return Response("Ricontrolla i campi inseriti.", status=403)

        try:
            if(content != None):
                update = Tile.query.filter_by(id = id).update(dict(title=title, author=author, content=content, category=category, media_type=media_type, board=board))
            else:
                update = Tile.query.filter_by(id = id).update(dict(title=title, author=author, category=category, media_type=media_type, board=board))
            db.session.commit()
        except Exception as e:
            return Response("Error" + str(e), status=403)
        return render_template("index.html")
    elif(request.method == 'GET'):
        return render_template('edit_tile.html')

@app.route('/api/v1/get_boards', methods = ['GET'])
def get_boards():
    boards = Board.query.order_by('id').all()
    board_list = []
    
    for board in boards:
        board_list.append(alchemy_board(board))

    return(json.dumps(board_list))

@app.route('/api/v1/get_tiles', methods = ['GET'])
def get_tiles():
    board = request.args.get('board')
    try:
        tiles = tiles_map()[board]
    except KeyError:
        return(json.dumps({}))
    dictionary = {}
    for x in tiles:
        dictionary[x.id] = alchemy_dict(x)
    return (json.dumps(dictionary))

@app.route('/api/v1/retrieve_tile', methods=['GET']) # ritorna contenuto di una tile a partire dall'id
def retrieve_tile():
    id = request.args.get('id')
    if(id):
        tile = Tile.query.filter_by(id=id).first()
        return Response(json.dumps(alchemy_dict(tile)), status=200)
    else:
        return Response("Ricontrolla i campi inseriti.", status=403)

@app.route('/api/v1/delete_tile', methods=['DELETE'])
def delete_tile():
    id = request.args.get('id')
    try:
        Tile.query.filter_by(id=id).delete()
        db.session.commit()
    except Exception as e:
        return Response("Error" + str(e), status=403)
    return Response(status=200)

@app.route('/api/v1/delete_board', methods=['DELETE'])
def delete_board():
    title = request.args.get('name')
    try:
        Board.query.filter_by(title=title).delete()
        Tile.query.filter_by(board=title).delete()
        db.session.commit()
    except Exception as e:
        return Response("Error" + str(e), status=403)
    return Response(status=200)

@app.route('/api/v1/archive_board', methods=['POST'])
def archive_board():
    title = request.args.get('name')
    try:
        board = Board.query.filter_by(title=title).filter_by(status=1).update(dict(status=0))
        db.session.commit()
    except Exception as e:
        return Response("Error", status=403)
    return Response(status=200)

@app.route('/api/v1/activate_board', methods=['POST'])
def activate_board():
    title = request.args.get('name')
    try:
        board = Board.query.filter_by(title=title).filter_by(status=0).update(dict(status=1))
        db.session.commit()
    except Exception as e:
        return Response("Error", status=403)
    return Response(status=200)

@app.route('/api/v1/rename_board', methods=['PUT'])
def rename_board():
    # rinomino la board nelle tile
    # rinomino la board
    old_board = request.args.get('old')
    new_board = request.args.get('new')
    
    if(Board.query.filter_by(title=new_board).first() != None):
        return Response("La colonna esiste già tra le attive o le archiviate. \nPer favore, usa un nome differente.", status=403)

    try:
        board = Board.query.filter_by(title=old_board).update(dict(title=new_board))
        db.session.commit()
    except Exception as e:
        return Response("Error board name update", status=403)

    try:
        board = Tile.query.filter_by(board=old_board).update(dict(board=new_board))
        db.session.commit()
    except Exception as e:
        return Response("Error board name update on tile", status=403)
    return Response(status=200)

if __name__ == "__main__":
    if(not os.path.isfile('kanban.db')): # crea il file db
        db.create_all()
    app.run(debug=True)