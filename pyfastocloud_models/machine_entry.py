from pymodm import EmbeddedMongoModel, fields
from pymodm.errors import ValidationError

from pyfastocloud_models.common_entries import Maker


class Machine(EmbeddedMongoModel, Maker):
    CPU_FIELD = 'cpu'
    GPU_FIELD = 'gpu'
    LOAD_AVERAGE_FIELD = 'load_average'
    MEMORY_TOTAL_FIELD = 'memory_total'
    MEMORY_FREE_FIELD = 'memory_free'
    HDD_TOTAL_FIELD = 'hdd_total'
    HDD_FREE_FIELD = 'hdd_free'
    BANDWIDTH_IN_FIELD = 'bandwidth_in'
    BANDWIDTH_OUT_FIELD = 'bandwidth_out'
    UPTIME_FIELD = 'uptime'
    TIMESTAMP_FIELD = 'timestamp'
    TOTAL_BYTES_IN_FIELD = 'total_bytes_in'
    TOTAL_BYTES_OUT_FIELD = 'total_bytes_out'

    class Meta:
        allow_inheritance = True

    cpu = fields.FloatField(required=True)
    gpu = fields.FloatField(required=True)
    load_average = fields.CharField(required=True)
    memory_total = fields.IntegerField(required=True)
    memory_free = fields.IntegerField(required=True)
    hdd_total = fields.IntegerField(required=True)
    hdd_free = fields.IntegerField(required=True)
    bandwidth_in = fields.IntegerField(required=True)
    bandwidth_out = fields.IntegerField(required=True)
    uptime = fields.IntegerField(required=True)
    timestamp = fields.IntegerField(required=True)
    total_bytes_in = fields.IntegerField(required=True)
    total_bytes_out = fields.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(Machine, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, cpu = self.check_required_type(Machine.CPU_FIELD, float, json)
        if res:
            self.cpu = cpu

        res, gpu = self.check_required_type(Machine.GPU_FIELD, float, json)
        if res:
            self.gpu = gpu

        res, load_average = self.check_required_type(Machine.LOAD_AVERAGE_FIELD, str, json)
        if res:
            self.load_average = load_average

        res, memory_total = self.check_required_type(Machine.MEMORY_TOTAL_FIELD, int, json)
        if res:
            self.memory_total = memory_total

        res, memory_free = self.check_required_type(Machine.MEMORY_FREE_FIELD, int, json)
        if res:
            self.memory_free = memory_free

        res, hdd_total = self.check_required_type(Machine.HDD_TOTAL_FIELD, int, json)
        if res:
            self.hdd_total = hdd_total

        res, hdd_free = self.check_required_type(Machine.HDD_FREE_FIELD, int, json)
        if res:
            self.hdd_free = hdd_free

        res, bandwidth_in = self.check_required_type(Machine.BANDWIDTH_IN_FIELD, int, json)
        if res:
            self.bandwidth_in = bandwidth_in

        res, bandwidth_out = self.check_required_type(Machine.BANDWIDTH_OUT_FIELD, int, json)
        if res:
            self.bandwidth_out = bandwidth_out

        res, uptime = self.check_required_type(Machine.UPTIME_FIELD, int, json)
        if res:
            self.uptime = uptime

        res, timestamp = self.check_required_type(Machine.TIMESTAMP_FIELD, int, json)
        if res:
            self.timestamp = timestamp

        res, total_bytes_in = self.check_required_type(Machine.TOTAL_BYTES_IN_FIELD, int, json)
        if res:
            self.total_bytes_in = total_bytes_in

        res, total_bytes_out = self.check_required_type(Machine.TOTAL_BYTES_OUT_FIELD, int, json)
        if res:
            self.total_bytes_out = total_bytes_out

    @staticmethod
    def default():
        return Machine(cpu=0.0, gpu=0.0, load_average=str(),
                       memory_total=0, memory_free=0,
                       hdd_total=0, hdd_free=0,
                       bandwidth_in=0, bandwidth_out=0,
                       uptime=0, timestamp=0,
                       total_bytes_in=0, total_bytes_out=0)
