from audio.model import Language
from .resources import IMotor, IOled, ISonic, IAudio, ISttAPI
    
class VisionTestBase:
    """
    Providing hardwares and OS resources
    """
    motor: IMotor
    oled: IOled
    sonic: ISonic
    audio: IAudio
    stt: ISttAPI

    def __init__(
            self,
            motor: IMotor | None = None,
            oled: IOled | None = None,
            sonic: ISonic | None = None,
            audio: IAudio | None = None,
            stt: ISttAPI | None = None
        ) -> None:

        self.motor = motor if motor is not None else IMotor()
        self.oled = oled if oled is not None else IOled()
        self.sonic = sonic if sonic is not None else ISonic()
        self.audio = audio if audio is not None else IAudio()
        self.stt = stt if stt is not None else ISttAPI()
    
class VisionTest(VisionTestBase):
    cur_distance: float
    cur_degree: float
    max_degree: float
    state: int
    dir: int
    lang: Language

    got_resp: bool | None
    phone_controller: any  # 手機控制器引用（如果是手機模式）

    def __init__(self, *args, **kwargs):
        # 提取 phone_controller 參數
        self.phone_controller = kwargs.pop('phone_controller', None)
        
        super().__init__(*args, **kwargs)

        self.max_degree = -1.0
        self.state = 0

        self.got_resp = None
        self.dir = 0
    
class InterruptException(Exception):
    end: bool
    test: VisionTest
    phone_mode: bool
    
    def __init__(self, *args, end: bool, test: VisionTest, phone_mode: bool = False):
        super().__init__(*args)
        self.end = end
        self.test = test
        self.phone_mode = phone_mode