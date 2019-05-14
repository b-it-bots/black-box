from __future__ import print_function

from importlib import import_module
import rospy

from black_box.config.config_utils import ConfigUtils

class TopicPublisher(object):

    """Publish a particular topic for a definite amount of time with a certain 
    frequency or for a definite number of times.
    :topic_name: string (topic where the message needs to be published)
    :msg_pkg: string (package from where the msg type can be imported)
    :msg_type: string (type of message to be published)

    :keyword arguments:
    :num_of_msgs: int (num of messages that needs to be published)
    :max_frequency: float (how many msgs should be be published in a second)
    """

    def __init__(self, topic_name, msg_pkg, msg_type, *args, **kwargs):
        # class variables
        self.topic_name = topic_name
        self.msg_pkg = msg_pkg
        self.msg_type = msg_type
        self.num_of_msgs = kwargs.get('num_of_msgs', 10)
        self.sleep_time = 1.0/kwargs.get('max_frequency', 10)
        self.publishing = False

        # creating publisher
        rospy.loginfo('Starting publisher of ' + self.topic_name)
        msg_module = import_module(self.msg_pkg)
        self.msg_class = getattr(msg_module, self.msg_type)
        self.publisher = rospy.Publisher(self.topic_name, self.msg_class, queue_size=1)

    def start(self):
        '''publish empty messages.
        '''
        self.publishing = True
        for i in range(self.num_of_msgs):
            if rospy.is_shutdown() or not self.publishing:
                break
            msg = self.msg_class()
            self.publisher.publish(msg)
            rospy.sleep(self.sleep_time)
        self.publishing = False
        
if __name__ == "__main__":
    topic_name = '/ropod/laser/scan'

    rospy.init_node(ConfigUtils.get_full_variable_name('topic_publisher', topic_name))
    topic_pub = TopicPublisher(
            topic_name,
            'sensor_msgs.msg', 
            'LaserScan', 
            num_of_msgs=100)
    topic_pub.start()
