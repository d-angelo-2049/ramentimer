# ra-men_timer.py
import RPi.GPIO as GPIO
import wiringpi as pi
import i2c_lcd
import asyncio

class RamenTimer:
    # pins
    LED_PIN = 23
    SW_PIN = 24
    BZ_PIN = 26
    IS_STARTED = False
    IS_READY = False
    
    def __init__(self):
        
        # setup 
        pi.wiringPiSetupGpio()
        pi.pinMode(self.LED_PIN, pi.OUTPUT)
        pi.pinMode(self.LED_PIN, pi.OUTPUT)
        pi.softPwmCreate(self.LED_PIN, 0, 100)
        pi.pinMode(self.SW_PIN, pi.INPUT)
        pi.pinMode(self.BZ_PIN, pi.OUTPUT)
        
        # lcd init
        i2c_lcd.lcd_init()

        # sw setting
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SW_PIN, GPIO.IN, GPIO.PUD_UP) 
        GPIO.add_event_detect(self.SW_PIN, GPIO.FALLING, bouncetime=1000)

    async def executor(self):
        print("activated!")
        self.event_loop = asyncio.get_event_loop()
        GPIO.add_event_callback(self.SW_PIN, callback=lambda c: self.event_loop.create_task(self.on_click(c)))
        while True:
            await asyncio.sleep(0.005)
            
    def clean(self):
        i2c_lcd.lcd_clear()
        GPIO.cleanup()
        
    async def on_click(self, channel):
        # pylint: disable=unused-argument
        print("on click")
        if (self.is_started_ra_men_timer() and not self.is_ready()):
            self.event_loop.create_task(self.show("Please wait until", "ramen ready."))
        elif (self.is_ready()):
            await self.stop_ra_men_timer()
        else:
            await self.start_ra_men_timer()
        
    def is_started_ra_men_timer(self):
        return self.IS_STARTED
    
    def is_ready(self):
        return self.IS_READY
            
    async def start_ra_men_timer(self):
        self.event_loop.create_task(self.show("Start timer", "wait a 3min"))
        self.IS_STARTED = True
        await self.wait_for_ready()
        self.on_ready()
        
    async def stop_ra_men_timer(self):
        self.IS_READY = False
        self.turn_off_buzzer()
        self.turn_off_led()
        self.IS_STARTED = False
        self.event_loop.create_task(self.show("Stopped timer", "bring up!")) 
        await asyncio.sleep(3)
        if(not self.is_started_ra_men_timer()):
            i2c_lcd.lcd_clear()
        
    async def auto_stop(self):
        await asyncio.sleep(10)
        if (self.is_ready()):
            await self.stop_ra_men_timer()
            
    async def wait_for_ready(self):
        await asyncio.sleep(180)
        
    def on_ready(self):
        self.event_loop.create_task(self.show("Your Ramen ready", "please push sw"))
        self.IS_READY = True
        self.event_loop.create_task(self.notify_the_user_ramen_on_ready())
        self.event_loop.create_task(self.auto_stop())
            
        
    async def notify_the_user_ramen_on_ready(self):
        self.turn_on_buzzer()
        value = 0
        while (self.is_ready()):
            while (value < 100 and self.is_ready()):
                pi.softPwmWrite(self.LED_PIN, value)
                await asyncio.sleep(0.05)
                value = value + 1
            while (value > 0 and self.is_ready() ):
                pi.softPwmWrite(self.LED_PIN, value)
                await asyncio.sleep(0.05)
                value = value - 1
                
    async def show(self, line1:str, line2:str):
        i2c_lcd.lcd_both_string(line1, i2c_lcd.LCD_LINE_1, line2, i2c_lcd.LCD_LINE_2)
        
    def turn_off_led(self):
        pi.softPwmWrite(self.LED_PIN, pi.LOW)

    def turn_on_buzzer(self):
        pi.digitalWrite(self.BZ_PIN, pi.HIGH)

    def turn_off_buzzer(self):
        pi.digitalWrite(self.BZ_PIN, pi.LOW)

if __name__ == '__main__':
    
    timer = RamenTimer()
    try:
        # execute
        asyncio.run(timer.executor())
    except KeyboardInterrupt:
        print("Terminated by Keyboard Interrupt")
    finally:
        timer.clean()


