from urllib.parse import urlparse
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, ValidationError, EmailField
from wtforms.validators import InputRequired

from gdshowreelvote.database import DB, Showreel, ShowreelStatus
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


def validate_store_urls(form, field):
    # Form is submitted with format: "url1;url2;url3"
    if field.data:
        urls = field.data.split(';')
        for url in urls:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError(f'Invalid URL: {url}')

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
    store_link = StringField('Store Link', validators=[InputRequired(), validate_store_urls])


class ManageShowreelsForm(FlaskForm):
    showreel_id = SelectField('Showreel', validators=[InputRequired()], choices=[])
    showreel_status = SelectField('Showreel Status', validators=[InputRequired()], 
                                  choices=[
                                      (ShowreelStatus.OPENED_TO_SUBMISSIONS.value, ShowreelStatus.OPENED_TO_SUBMISSIONS.value),
                                      (ShowreelStatus.VOTE.value, ShowreelStatus.VOTE.value),
                                      (ShowreelStatus.CLOSED.value, ShowreelStatus.CLOSED.value)
                                  ])

    def validate(self, extra_validators = None):
        if not super().validate(extra_validators):
            return False

        submissions = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS).first()
        if submissions and self.showreel_status.data == ShowreelStatus.OPENED_TO_SUBMISSIONS.value:
            self.showreel_status.errors.append("There is already a showreel open for submissions.")
            return False

        vote = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.VOTE).first()
        if vote and self.showreel_status.data == ShowreelStatus.VOTE.value:
            self.showreel_status.errors.append("There is already a showreel open for voting.")
            return False

        return True
