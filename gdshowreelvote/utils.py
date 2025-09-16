from typing import Dict, List, Tuple
from sqlalchemy import and_, func
from gdshowreelvote.database import DB, Showreel, ShowreelStatus, User, Video, Vote


def choose_random_video(user: User, skip_videos: List[int]=[]) -> Video:
    """ Choose a random video from the showreel that the user has not voted on yet. """
    # Is there any chance that there are multiple showreels in VOTE status?
	# Should we choose the showreel with a specific ID?
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
    vote = DB.session.query(Vote).filter(and_(Vote.user_id == user.id, Vote.video_id == video.id)).first()
    if vote:
        vote.rating = 1
    else:
        vote = Vote(user_id=user.id, video_id=video.id, rating=1)
        DB.session.add(vote)
    DB.session.commit()
    return vote


def downvote_video(user: User, video: Video):
    """ Cast a downvote for a video by a user. """
    vote = DB.session.query(Vote).filter(and_(Vote.user_id == user.id, Vote.video_id == video.id)).first()
    if vote:
        vote.rating = -1
    else:
        vote = Vote(user_id=user.id, video_id=video.id, rating=-1)
        DB.session.add(vote)
    DB.session.commit()
    return vote


def _video_data(video: Video) -> Dict:
    data = {
            'id': video.id,
            'game': video.game,
            'author': video.author_name,
            'follow_me_link': video.follow_me_link,
            'video_link': video.video_link,
            'store_link': video.store_link,
            'category': video.showreel.title,
        }
        # TODO: Need to make sure we extract the YouTube ID correctly
    youtube_id = video.video_link.split('v=')[-1]
    data['youtube_embed'] = f'https://www.youtube.com/embed/{youtube_id}'
    return data


def vote_data(user: User, video: Video) -> Tuple[Dict, Dict]:
    total_video_count = DB.session.query(Video).count()
    total_user_votes = DB.session.query(Vote).filter(Vote.user_id == user.id).count()

    data = _video_data(video) if video else None

    progress = {
		'total': total_video_count, 
		'current': total_user_votes + 1,
	}
    
    return data, progress
