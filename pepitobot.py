import os
import pyotp
from time import sleep
from twitter import Twitter, OAuth
import vrchatapi
from vrchatapi import TwoFactorAuthCode
from vrchatapi.api import authentication_api, groups_api
from vrchatapi.models import UpdateGroupRequest
from vrchatapi.exceptions import UnauthorizedException

PEPITO_STATUS_OUT = 'Pépito is out'
PEPITO_STATUS_BACK = 'Pépito is back home'
PEPITO_STATUS_UNKNOWN = 'Pépito is ❓'
PEPITO_VALID_STATUSES = [PEPITO_STATUS_OUT, PEPITO_STATUS_BACK]
PEPITO_TWITTER_USERNAME = 'PepitoTheCat'


def auth_to_twitter_api(consumer_key, consumer_secret):
    print("Logging into Twitter API.")
    return Twitter(retry=True, auth=OAuth(
        token='', token_secret='',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret))


def get_pepito_latest_tweet(twitter):
    print("Getting latest Pépito tweet id...")
    params = {'fields': ['most_recent_tweet_id']}
    return twitter.users.show(screen_name=PEPITO_TWITTER_USERNAME, user=params)


def pepito_status_from_tweet_text(text):
    if ('is out' in text):
        return PEPITO_STATUS_OUT
    elif ('back home' in text):
        return PEPITO_STATUS_BACK
    else:
        return PEPITO_STATUS_UNKNOWN


def do_vrc_auth(vrc_client, totp_key):
    vrc_auth_api = authentication_api.AuthenticationApi(vrc_client)
    try:
        return vrc_auth_api.get_current_user()
    except UnauthorizedException:
        totp = pyotp.TOTP(totp_key)
        number = totp.now()
        print(f"VRC Login Unauthorized, doing 2FA dance...")
        vrc_auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(number))
        print("2FA verified, redoing auth...")
        return vrc_auth_api.get_current_user()


def set_vrc_group(vrc_client, totp_key, group_id, new_status):
    print(f"Updating VRC Pepito status to: [{new_status}]")
    do_vrc_auth(vrc_client, totp_key)
    vrc_grp_api = groups_api.GroupsApi(vrc_client)
    ugr = UpdateGroupRequest(name=new_status)
    return vrc_grp_api.update_group(group_id, update_group_request=ugr)


def main():
    print("PepitoBot SETUP START!")
    TWITTER_BOT_API_KEY = os.environ['PEPITO_TWITTER_BOT_API_KEY']
    TWITTER_BOT_API_SECRET = os.environ['PEPITO_TWITTER_BOT_API_SECRET']

    POLL_DELAY_SEC = float(os.environ.get('PEPITO_POLL_DELAY_SEC', '65.0'))

    VRC_GROUP_ID = os.environ['PEPITO_VRC_GROUP_ID']

    VRC_USERNAME = os.environ['PEPITO_VRC_USERNAME']
    VRC_PASSWORD = os.environ['PEPITO_VRC_PASSWORD']
    VRC_2FAKEY = os.environ['PEPITO_VRC_2FAKEY']

    VRC_CONFIG = vrchatapi.Configuration(
        username=VRC_USERNAME,
        password=VRC_PASSWORD,
    )

    first_loop = True
    pepito_is = PEPITO_STATUS_UNKNOWN
    last_pepito_tweet_id = None

    twtr = auth_to_twitter_api(
        consumer_key=TWITTER_BOT_API_KEY, consumer_secret=TWITTER_BOT_API_SECRET)

    with vrchatapi.ApiClient(VRC_CONFIG) as vrc_api:
        print("PepitoBot MAIN LOOP START!")
        while (True):
            if (not first_loop):
                print(
                    f"Waiting {POLL_DELAY_SEC}s before checking again...")
                sleep(POLL_DELAY_SEC)
            else:
                first_loop = False

            latest_pepito_tweet = get_pepito_latest_tweet(twitter=twtr)['status']
            latest_pepito_tweet_id = latest_pepito_tweet['id_str']
            latest_pepito_tweet_text = latest_pepito_tweet['text']
            print(f"Got tweet: [{latest_pepito_tweet_id}]")

            if (latest_pepito_tweet_id == last_pepito_tweet_id):
                print("Same tweet as last time we checked, nothing to do.")
                continue

            last_pepito_tweet_id = latest_pepito_tweet_id
            print(f"New tweet! ID:[{last_pepito_tweet_id}]")

            new_status = pepito_status_from_tweet_text(
                latest_pepito_tweet_text)

            if (new_status not in PEPITO_VALID_STATUSES):
                print("New state invalid, skipping VRC update")
                continue

            if (new_status == pepito_is):
                print("New status same as current, skipping VRC update")
                continue

            print("Valid new state recognized.")

            pepito_is = new_status
            set_vrc_group(vrc_client=vrc_api, totp_key=VRC_2FAKEY,
                          group_id=VRC_GROUP_ID, new_status=new_status)
            print("Group Name Updated!")


if __name__ == "__main__":
    main()
