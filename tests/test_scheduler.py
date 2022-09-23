import time

from dream.components.load_balancer import LeastConnectionScheduler


def test_least_connection():
    mock_servers = {"url1": 10, "url2": 5}

    class MockLeastConnectionScheduler(LeastConnectionScheduler):
        def update_backlog(self):
            self.server_backlogs = mock_servers

    scheduler = MockLeastConnectionScheduler(list(mock_servers.keys()), update_interval=1)
    time.sleep(1)
    assert scheduler.get_server() == "url2"

    mock_servers = {"url1": 1, "url2": 6}
    scheduler.update_backlog()
    time.sleep(1)
    assert scheduler.get_server() == "url1"
