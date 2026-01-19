from urllib.parse import urlparse
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, ValidationError, EmailField
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
        

def validate_urls(form, field):
    if field.data:
        parsed = urlparse(field.data)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValidationError(f'Invalid URL: {field.data}')


class CastVoteForm(FlaskForm):
    action = StringField('Action', validators=[validate_action])
    video_id = IntegerField('Video ID', validators=[InputRequired()])


class SelectVideoForm(FlaskForm):
    video_id = IntegerField('Video ID', validators=[InputRequired()])


class VideoSubmissionForm(FlaskForm):
    game = StringField('Game Title', validators=[InputRequired()])
    author_name = StringField('Author Name', validators=[InputRequired()])
    contact_email = EmailField('Contact Email', validators=[InputRequired()])
    video_link = StringField('Video Link', validators=[InputRequired(), validate_urls])  # TODO: Check specific URL formats
    video_download_link = StringField('Video Download Link', validators=[InputRequired(), validate_urls])
    follow_me_link = StringField('Follow Me Link', validators=[InputRequired(), validate_urls])
    store_link = StringField('Store Link', validators=[InputRequired(), validate_urls])
