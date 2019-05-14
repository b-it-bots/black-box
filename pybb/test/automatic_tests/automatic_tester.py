from multiprocessing import Process, Queue
import threading
import rospy
import sys
import psutil
from termcolor import colored

from topic_publisher import TopicPublisher

from black_box.config.config_file_reader import ConfigFileReader
from black_box.config.config_params import RosTopicParams
from black_box.config.config_utils import ConfigUtils
from black_box_tools.db_utils import DBUtils

class AutomaticTester(object):
    '''An interface to manage all publishers

    Constructor arguments:
    @param config_params -- an instance of black_box.config.config_params.RosParams

    '''
    def __init__(self, config_params, duration):
        self.config_params = config_params
        self.duration = duration
        self.publishers = []
        self.publisher_threads = []
        rospy.init_node('automatic_tester')

        # initialising publishers
        for topic_params in self.config_params.topic:
            num_of_msgs = self.duration * topic_params.max_frequency
            publisher = TopicPublisher(
                    topic_params.name,
                    topic_params.msg_pkg,
                    topic_params.msg_type,
                    num_of_msgs=num_of_msgs,
                    max_frequency=topic_params.max_frequency,
                    )
            pub_thread = threading.Thread(target=publisher.start)
            self.publishers.append(publisher)
            self.publisher_threads.append(pub_thread)

    def start(self):
        '''Starts and runs the publishers on background threads
        '''
        for pub_thread in self.publisher_threads:
            pub_thread.start()

    def stop(self):
        """Wait for all pub to complete.
        :returns: None

        """
        for pub_thread in self.publisher_threads:
            pub_thread.join()

def is_bb_running():
    """Checks in all processes if black box is one of the process or not
    :returns: bool

    """
    processes = list(psutil.process_iter())
    bb_processes = [process for process in processes if 'logger_main.py' in process.cmdline()]
    return len(bb_processes) > 0

def check_logs(config_params, test_duration):
    """Check the logs in mongodb and print the status.

    :config_params: black_box.config.ConfigParams
    :test_duration: float
    :returns: None

    """
    db_name = config_params.default.db_name
    collection_names = DBUtils.get_data_collection_names(db_name)

    # check if all topics are present in db
    fail = False
    size_status = []
    for topic_params in config_params.ros.topic:
        topic_name = ConfigUtils.get_full_variable_name("ros", topic_params.name)
        if topic_name not in collection_names:
            fail = True
            print(colored(topic_name + " not present in mongoDB", "red"))
            size_status.append({
                'expected_size':topic_params.max_frequency*test_duration,
                'collection_size':0})
            continue
        collection_size = len(DBUtils.get_all_docs(db_name, topic_name))
        size_status.append({
                'expected_size':topic_params.max_frequency*test_duration,
                'collection_size':collection_size})
    if not fail:
        print(colored("All topics have their respective collection in mongoDB", "green"))
    for comparison in size_status:
        color = "green" if comparison['expected_size'] == comparison['collection_size'] else "red"
        print(colored(comparison, color))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 automatic_tester.py [absolute-path-to-black-box-config-file]')
        sys.exit(1)
    bb_config_file = sys.argv[1]

    test_duration = 20 #seconds

    # only proceed if black box is running
    if not is_bb_running():
        print('Blackbox is not running. Please make sure it is running before executing this test script.')
        sys.exit(1)
    
    config_params = ConfigFileReader.load_config(bb_config_file)
    DBUtils.clear_db(config_params.default.db_name)

    tester = AutomaticTester(config_params.ros, test_duration)
    print("initialised all publisher")

    tester.start()
    print("publishers running")

    tester.stop()
    print("publishers stopped")

    check_logs(config_params, test_duration)
