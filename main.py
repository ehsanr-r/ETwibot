
import tweepy
import pandas as pd
import asyncio
import websockets
import webbrowser
import logging


class Etwibot:
    consumer_key = "DhpMzV3ZcLP*****************"
    consumer_secret = "SLS4Zd61JjIs4tSjAjyey9A***************************"
    bearer_token = "AAAAAAAAAAAAAAAAAAAAACfBbgEAAAAABBUx3re15WC7XlF5ZSZ************************************************"
    oauth1_user_handler = None
    api = None
    new_status = None
    user = None
    user_timeline = None
    screen_name = None
    client = None
    websocket = None

    def __init__(self, name):
        self.screen_name = name

    def get_authentication_url(self):
        try:
            self.oauth1_user_handler = tweepy.OAuth1UserHandler(
                self.consumer_key, self.consumer_secret,
                callback="oob",
            )

            return self.oauth1_user_handler.get_authorization_url()
        except:
            return "Url Error"

    def authenticate_user(self, pin):

        try:
            # get verifier with url
            # request_token = oauth1_user_handler.request_token["oauth_token"]
            # request_secret = oauth1_user_handler.request_token["oauth_token_secret"]

            access_token, access_token_secret = self.oauth1_user_handler.get_access_token(pin)
            # print(access_token)
            # print(access_token_secret)

            self.api = tweepy.API(self.oauth1_user_handler)

            self.client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            # print(dir(self.client))
            # print(self.client.get_me().data.name)

            self.api.verify_credentials()
            return "Authentication Successful"

        except Exception as e:
            return "Authentication Error"

    def update_status(self, tweet):
        # print("Updating status: ")
        try:
            # self.new_status = self.api.update_status(status=tweet)
            self.new_status = self.client.create_tweet(text=tweet)
            # print(dir(self.new_status.data))
            return "Update Successful"
        except:
            return "Update Error!!!"

    def destroy_status(self, id_tweet):
        # print("Destroying status: ")
        try:
            self.client.delete_tweet(id=id_tweet)
            return "Destroy Successful"
        except:
            return "Destroy Error!!!"

    def print_user_info(self):
        # print("Printing user info: ")
        try:
            # self.user = self.api.get_user(screen_name=self.screen_name)
            # print(dir(self.user))
            # print(dir(self.api))
            # print(dir(self.client.get_me().data))
            user_id = self.client.get_me().data.id
            user_name = self.client.get_me().data.name
            return "Twitter name is " + user_name + " and Twitter id is : " + str(user_id)
        except:
            return "Info Error!!!"

    def print_user_timeline(self):
        # print("Printing timeline: ")
        try:
            self.user = self.api.get_user(screen_name=self.screen_name)
            self.user_timeline = self.user.timeline()
            # self.user_timeline = self.client.get_users_tweets(id=self.client.get_me().data.id)
            # print(dir(user_timeline))
            columns = set()
            allowed_types = [str, int]
            tweets_data = []
            for status in self.user_timeline:
                # print(status.text)
                # print(vars(status))
                status_dict = dict(vars(status))
                keys = status_dict.keys()
                single_tweet_data = {"user": status.user.screen_name, "author": status.author.screen_name}
                for k in keys:
                    try:
                        v_type = type(status_dict[k])
                    except:
                        v_type = None
                    if v_type is not None:
                        if v_type in allowed_types:
                            single_tweet_data[k] = status_dict[k]
                            columns.add(k)
                tweets_data.append(single_tweet_data)

            header_columns = list(columns)
            header_columns.append("user")
            header_columns.append("author")

            df = pd.DataFrame(tweets_data, columns=header_columns)
            df.head()
            return df.to_string()
        except:
            return "Timeline Error!!!"

    def print_status_data(self, tweet_id):
        # data = "Printing tweet data: " + "\n"
        try:
            # status_obj_id = self.user_timeline[0].id
            status_obj_id = tweet_id
            status_obj = self.api.get_status(id=status_obj_id, tweet_mode='extended')
            data = "Text: " + status_obj.full_text + "\n"
            data += "Favorite: " + str(status_obj.favorite_count) + "\n"
            data += "Retweet: " + str(status_obj.retweet_count) + "\n"
            # print(dir(status_obj))
            if 'media' in status_obj.entities:
                media_details = status_obj.entities['media']
                data += media_details[0]['media_url'] + "\n"
            else:
                data += "No Media" + "\n"

            data += "Printing tweet replies: " + "\n"
            replies = []
            for reply in tweepy.Cursor(self.api.search_tweets, q='to:' + self.screen_name, result_type='recent',
                                       timeout=999999).items(1000):
                if hasattr(reply, 'in_reply_to_status_id_str'):
                    # if reply.in_reply_to_status_id_str == status_obj_id:
                    replies.append(reply)
            if len(replies) > 0:
                for reply in replies:
                    data += reply.text + "\n"
            else:
                data += "No Replies" + "\n"
            return data
        except:
            return "Status Data Error!!!"


async def connect_to_server():

    uri = "ws://localhost:8766"

    async with websockets.connect(uri) as websocket:

        name = input("What's your name? ")

        await websocket.send(name)
        print(f">>> {name}")

        greeting = await websocket.recv()
        print(f"<<< {greeting}")

        user_name = await websocket.recv()
        print(f"<<< Username: {user_name}")

        tweet_text = await websocket.recv()
        print(f"<<< Tweet text: {tweet_text}")

        tweet_id = await websocket.recv()
        print(f"<<< Tweet id: {tweet_id}")

        etwibot = Etwibot(name=user_name)

        url = etwibot.get_authentication_url()
        await websocket.send(url)
        print(f">>> {url}")

        pin = await websocket.recv()
        print(f"<<< Pin: {pin}")

        auth = etwibot.authenticate_user(pin=pin)
        await websocket.send("Authenticating user ...\n" + auth)
        print(f">>> {auth}")

        user_info = etwibot.print_user_info()
        await websocket.send("Printing user info ...\n" + user_info)
        print(f">>> {user_info}")

        timeline = etwibot.print_user_timeline()
        await websocket.send("Printing user timeline ...\n" + timeline)
        print(f">>> {timeline}")

        status = etwibot.print_status_data(tweet_id=tweet_id)
        await websocket.send("Printing status data ...\n" + status)
        print(f">>> {status}")

        update = etwibot.update_status(tweet=tweet_text)
        await websocket.send("Updating status ...\n" + update)
        print(f">>> {update}")


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger("tweepy")
    # logger.setLevel(logging.DEBUG)
    # handler = logging.FileHandler(filename="tweepy.log")
    # logger.addHandler(handler)
    app_name = "Ehsan + Twitter + Bot = Etwibot"
    print(app_name)

    asyncio.run(connect_to_server())

