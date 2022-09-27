import uuid
from typing import Dict

from lightning import LightningFlow


class WorkManager(LightningFlow):
    def __init__(self, groups):
        super().__init__()

        self.groups = groups
        self.group = groups[0]

        # Maps collection name -> work name -> work attribute
        self.managed_works: Dict[str, Dict[str, str]] = {group: {} for group in self.groups}

    def register_work(self, work_name, work):
        group = self.group
        work_attribute = uuid.uuid4().hex
        if group not in self.managed_works:
            self.managed_works[group] = {}
        self.managed_works[group][str(work_name)] = work_attribute
        setattr(self, work_attribute, work)

    def get_work(self, work_name):
        group = self.group
        work_name = str(work_name)
        if group in self.managed_works and work_name in self.managed_works[group]:
            return getattr(self, self.managed_works[group][work_name], None)
        return None

    def remove_work(self, work_name):
        work_name = str(work_name)
        del self.managed_works[self.group][work_name]

    @property
    def num_workers(self):
        return len(self.managed_works[self.group])

    @property
    def get_works(self):
        workers = []
        for i in range(self.num_workers):
            workers.append(self.get_work(self.group, i))
        return workers
