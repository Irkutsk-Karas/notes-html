from flask import jsonify
from flask_restful import Resource, abort, reqparse

from data import db_session
from data.notes import Note


def abort_if_note_not_found(note_id):
    session = db_session.create_session()
    news = session.query(Note).get(note_id)
    if not news:
        abort(404, message=f"Note {note_id} not found")


parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('is_private', type=bool)
parser.add_argument('user_id', required=True, type=int)


class NoteResource(Resource):
    def get(self, note_id):
        abort_if_note_not_found(note_id)
        session = db_session.create_session()
        note = session.query(Note).get(note_id)
        return jsonify({'note': note.to_dict(
            only=('title', 'content', 'user_id', 'is_private'))})

    def delete(self, note_id):
        abort_if_note_not_found(note_id)
        session = db_session.create_session()
        news = session.query(Note).get(note_id)
        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, note_id):
        abort_if_note_not_found(note_id)
        args = parser.parse_args()
        session = db_session.create_session()
        note = session.query(Note).get(note_id)
        note.title = args['title']
        note.content = args['content']
        note.user_id = args['user_id']
        note.is_private = args['is_private']
        session.commit()
        return jsonify({'success': 'OK'})


class NoteListResource(Resource):
    def get(self):
        session = db_session.create_session()
        notes = session.query(Note).all()
        return jsonify({'notes': [item.to_dict(
            only=('title', 'content', 'user.name')) for item in notes]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        news = Note(
            title=args['title'],
            content=args['content'],
            user_id=args['user_id'],
            is_private=args['is_private']
        )
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})
