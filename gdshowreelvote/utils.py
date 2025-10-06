from urllib.parse import parse_qs, urlparse
from werkzeug.exceptions import NotFound

from typing import Dict, List, Optional, Tuple
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

    if random_video_without_votes is None:
        # If all videos have been voted on, return a random video that was skipped
        random_video_without_votes = (
            DB.session.query(Video)
            .join(Showreel, Video.showreel_id == Showreel.id)  # join explicitly
            .outerjoin(Vote, and_(Video.id == Vote.video_id, Vote.user_id == user.id))
            .filter(Showreel.status == ShowreelStatus.VOTE)  # filter on Showreel column
            .filter(Vote.rating == 0)  # check votes with rating 0 (skipped)
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


def skip_video(user: User, video: Video):
    vote = DB.session.query(Vote).filter(and_(Vote.user_id == user.id, Vote.video_id == video.id)).first()
    if vote:
        vote.rating = 0
    else:
        vote = Vote(user_id=user.id, video_id=video.id, rating=0)
        DB.session.add(vote)
    DB.session.commit()
    return vote


def video_data(video: Video) -> Dict:
    data = {
            'id': video.id,
            'game': video.game,
            'author': video.author_name,
            'follow_me_link': video.follow_me_link,
            'video_link': video.video_link,
            'store_link': video.store_link,
            'category': video.showreel.title,
        }

    youtube_id = parse_youtuvbe_video_id(video.video_link)
    data['youtube_embed'] = f'https://www.youtube.com/embed/{youtube_id}'
    return data


def vote_data(user: User, video: Video) -> Tuple[Dict, Dict]:
    total_video_count = DB.session.query(Video).count()
    total_user_votes = DB.session.query(Vote).filter(Vote.user_id == user.id).count()

    data = video_data(video) if video else None

    progress = {
		'total': total_video_count, 
		'current': total_user_votes,
	}
    
    return data, progress


def get_total_votes() -> Tuple[int, int, List[Tuple[Video, int, int]]]:
    total_votes = DB.session.query(func.count(Vote.id)).filter(Vote.rating != 0).scalar()
    positive_votes = DB.session.query(func.count(Vote.id)).filter(Vote.rating == 1).scalar()
    results = (
        DB.session.query(
            Video,
            func.coalesce(func.sum(Vote.rating), 0).label("vote_sum"),
            func.count(Vote.id).label("vote_count"),
        )
        .outerjoin(Vote, Vote.video_id == Video.id)
        .group_by(Video.id)
        .order_by(func.coalesce(func.sum(Vote.rating), 0).desc())
        .all()
    )

    return total_votes, positive_votes, results


def parse_youtuvbe_video_id(yt_url: str) -> Optional[str]:
    """
        Source: https://stackoverflow.com/questions/4356538/how-can-i-extract-video-id-from-youtubes-link-in-python/7936523#7936523
        Examples:
        - http://youtu.be/SA2iWivDJiE
        - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        - http://www.youtube.com/embed/SA2iWivDJiE
        - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(yt_url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None
