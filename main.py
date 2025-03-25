import os
from google.cloud import pubsub_v1

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
subscription_id = os.environ.get("PUBSUB_SUBSCRIPTION")

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received message: {message.data.decode('utf-8')}")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}...")

try:
    streaming_pull_future.result()  # Blocks indefinitely, or until an error occurs.
except Exception as e:
    print(f"Listening for messages failed: {e}")
    streaming_pull_future.cancel() # Cancel the subscriber client.
    streaming_pull_future.result() # block until cancelled.