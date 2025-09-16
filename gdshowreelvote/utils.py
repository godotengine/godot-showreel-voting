from typing import List
from sqlalchemy import and_, func
from gdshowreelvote.database import DB, Showreel, ShowreelStatus, User, Video, Vote


def choose_random_video(user: User, skip_videos: List[int]=[]) -> Video:
    """ Choose a random video from the showreel that the user has not voted on yet. """
    random_video_without_votes = (
        DB.session.query(Video)
        .join(Showreel, Video.showreel_id == Showreel.id)  # join explicitly
        .outerjoin(Vote, and_(Video.id == Vote.video_id, Vote.user_id == user.id))
        .filter(Showreel.status == ShowreelStatus.VOTE)  # filter on Showreel column
        .filter(Vote.id == None)  # exclude videos already voted on by this user
        .filter(Video.id.notin_(skip_videos))  # exclude skipped videos
        .order_by(func.random())
        .first()
    )

    return random_video_without_votes


def upvote_video(user: User, video: Video):
    """ Cast an upvote for a video by a user. """
    vote = Vote(user_id=user.id, video_id=video.id, rating=1)
    DB.session.add(vote)
    DB.session.commit()
    return vote


def downvote_video(user: User, video: Video):
    """ Cast a downvote for a video by a user. """
    vote = Vote(user_id=user.id, video_id=video.id, rating=-1)
    DB.session.add(vote)
    DB.session.commit()
    return vote

