from typing import Optional
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, ValidationError
from wtforms.validators import InputRequired

from gdshowreelvote.utils import downvote_video, skip_video, upvote_video


VOTE_ACTIONS = {
    'upvote': upvote_video,
    'downvote': downvote_video,
    'skip': skip_video
}

def validate_action(form, field):
    if field.data:
        if VOTE_ACTIONS.get(field.data) is None:
            raise ValidationError(f"Action '{field.data}' is not supported.")


class CastVoteForm(FlaskForm):
    action = StringField('Action', validators=[validate_action])
    video_id = IntegerField('Video ID', validators=[InputRequired()])


class SelectVideoForm(FlaskForm):
    video_id = IntegerField('Video ID', validators=[InputRequired()])