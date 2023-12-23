from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
import datetime
import pytz

app = Flask(__name__)
app.config["SECRET_KEY"] = "asdfghjkl"
socketio = SocketIO(app)

rooms={}

def generate_code(length):
    while True:
        code=""

        for _ in range (length):
            code+=random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method=="POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", name=name, code=code, error = "Please enter your name...")
        
        if join!=False and not code:
            return render_template("home.html", name=name, code=code, error = "Please enter a room code...")
        
        room=code
        if create!=False:
            room = generate_code(4)
            rooms[room]={"members":0, "messages":[]}

        elif code not in rooms:
            return render_template("home.html", name=name, code=code, error = "Room does not exist...")
        
        session["room"]=room
        session["name"]=name
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", room=room, messages=rooms[room]["messages"])


@socketio.on("new_message")
def new_message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    format = "%d-%m-%Y %H:%M:%S"
    time = current_time.strftime(format)

    content = {"name": session.get("name"), "message": data["data"], "time": time}
    send(content, to=room)
    rooms[room]["messages"].append(content)

    print(f"{session.get('name')} said {data['data']} at {time}")
    


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    rooms[room]["members"]+=1

    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    format = "%d-%m-%Y %H:%M:%S"
    time = current_time.strftime(format)

    content = {"name":name, "message": "joined the room", "time":time}
    send(content, to=room)
    rooms[room]["messages"].append(content)

    print(f"{name} has joined {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    leave_room(room)

    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"] <=0:
            del rooms[room]

    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    format = "%d-%m-%Y %H:%M:%S"
    time = current_time.strftime(format)

    content = {"name":name, "message": "left the room", "time":time}
    send(content, to=room)
    rooms[room]["messages"].append(content)

    print(f"{name} has joined {room}")


if __name__ == "__main__":
    socketio.run(app, debug=True)

