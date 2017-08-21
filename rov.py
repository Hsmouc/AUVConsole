# coding=UTF-8
from Tkinter import *
from PIL import Image,ImageTk
from numpy import *
import threading
import smbus
import math
import serial
import os

root = Tk()
root.configure(bg='white')
bus = smbus.SMBus(1)
cpu_temp_str = StringVar()
cabin_temp_str = StringVar()
RAM_used_str = StringVar()
RAM_free_str = StringVar()
water_temp_str = StringVar()
humidity_str = StringVar()
reverse_control_str = StringVar()
start_stop_str = StringVar()
yaw_str = StringVar()
roll_str = StringVar()
pitch_str = StringVar()
start_stop_str.set('Stop')
reverse_control_str.set('normal')
ser = serial.Serial("/dev/ttyAMA0",115200,timeout=0.1)
x_0,y_0 = 175,175
isZeroSet,isReverse,start_stop = 0,0,0
isTrajectoryClear = 0
AUV_yaw,AUV_roll,AUV_pitch = 0,0,0
zoom = 1
AUV_distance = 0
AUV_distance_cnt = 0
water_temperature,ht_select = 0,0

def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
	i = i + 1
	line = p.readline()
	if i==2:
	    return(line.split()[1:4])

def cpu_temperature_convert(origin):
    ip = int(origin)/1000
    dp = int(origin)%1000
    return str(ip)+'.'+str(dp)+'˚C'

def get_cpu_temperature():
    f = open('/sys/class/thermal/thermal_zone0/temp')
    cpu_temperature = f.readline()
    f.close()
    temperature = cpu_temperature_convert(cpu_temperature)
    return temperature

def select_humidity_temperature():
    global ht_select
    if ht_select == 0:
        bus.write_byte(0x40,0xF5)
    else:
	bus.write_byte(0x40,0xF3)
    root.after(500,select_humidity_temperature)

def get_humidity_temperature():
    global ht_select
    data0,data1 = 0,0
    try:
    	data0 = bus.read_byte(0x40)
    	data1 = bus.read_byte(0x40)
    except:
	pass
    if ht_select == 0:
    	result = ((data0*256+data1)*125/65536.0)-6
    else:
	result = ((data0*256+data1)*175.72/65536.0)-46.85
    return round(result,2)

def yaw_zero():
    global isZeroSet
    isZeroSet = 1    

def reverse_control():
    global isReverse
    if isReverse == 0:
    	isReverse = 1
	reverse_control_str.set('Reverse')
    else:
	isReverse = 0
	reverse_control_str.set('Normal')

def start_stop_control():
    global start_stop
    if start_stop == 0:
	start_stop = 1
	start_stop_str.set('start')
    else:
	start_stop = 0
	start_stop_str.set('stop')

def clear_trajectory():
    global isTrajectoryClear
    isTrajectoryClear = 1

def zoom_in():
    global zoom
    zoom = zoom*2
    if zoom > 16:
	zoom = 16

def zoom_out():
    global zoom
    zoom = zoom/2
    if zoom < 0.0625:
	zoom = 0.0625

def com_data_convert(data):
    if data < 10:
	str_data = '00'+str(data)
    if data >= 10 and data < 100:
	str_data = '0'+str(data)
    if data >= 100:
	str_data = str(data)
    return str_data

def fetch_values():
    global AUV_yaw,AUV_roll,AUV_pitch,water_temperature,AUV_distance,AUV_distance_cnt
    try:
        s = ser.readlines()
    except:
        pass
    if len(s) > 0:
        data = s[0].split('A')
        info = data[1].split('x')
	AUV_yaw = int(info[0])
	AUV_roll = int(info[2])-90
	AUV_pitch = int(info[3])-90
	AUV_distance = int(info[4])*int(info[5])
	water_temperature = int(info[1])
	AUV_distance_cnt = AUV_distance_cnt + 1    
    	if AUV_distance_cnt > 9:
	    AUV_distance_cnt = 0
    yaw_str.set(str(AUV_yaw)+'˚')
    roll_str.set(str(AUV_roll)+'˚')
    pitch_str.set(str(AUV_pitch)+'˚')
    print s
     
def send_values(root,GUI):
    global isZeroSet,isReverse,start_stop
    depth = GUI.w1.get()
    servo_1 = GUI.servo1.get()
    servo_2 = GUI.servo2.get()
    yaw = int(GUI.theta)+180
    speed = int(GUI.length)
    depth_str = com_data_convert(depth)
    speed_str = com_data_convert(speed)
    yaw_str = com_data_convert(yaw)
    servo_1_str = com_data_convert(servo_1)
    servo_2_str = com_data_convert(servo_2)
    isZeroSet_str = str(isZeroSet)
    isReverse_str = str(isReverse)
    start_stop_str = str(start_stop)
    package = 'A'+yaw_str+'x'+speed_str+'x'+depth_str+'x'+servo_1_str+'x'+servo_2_str+'x'+isZeroSet_str+'x'+isReverse_str+'x'+start_stop_str
    isZeroSet = 0
    print package
    ser.write(package)
    fetch_values()
    GUI.GUI_draw_trajectory(GUI,30,1,AUV_distance_cnt)#AUV_yaw,AUV_distance,AUV_distance_cnt)
    root.after(500,lambda:send_values(root,GUI))

class consoleGUI:
    def __init__(self,root):
        self.root = root
        self.root.geometry("1024x768+0+0")
	self.length = 0
	self.theta = 0
        t_name = Label(self.root,text='AUV Console',font=('Arial',15),bg='white')
	t_name.pack()

        t_ouc = Label(self.root,text='Ocean University of China',
        font=('Arial',10),bg='white')
        t_ouc.place(x=420,y=40)

        self.w1 = Scale(self.root, from_=0, to=100, length=200, tickinterval=5,bg='white',highlightthickness=0)
        self.w1.set(50)
        self.w1.place(x=300,y=80)

	self.servo1 = Scale(self.root, from_=0, to=100, length=270, tickinterval=10, 
			orient=HORIZONTAL,bg='white',highlightthickness=0)
        self.servo1.set(0)
        self.servo1.place(x=430,y=120)

	t_servo1 = Label(self.root,text='Arm',bg='white')
	t_servo1.place(x=430,y=100)

	self.servo2 = Scale(self.root, from_=0, to=100, length=270, tickinterval=10,
			 orient=HORIZONTAL,bg='white',highlightthickness=0)
        self.servo2.set(0)
        self.servo2.place(x=430,y=220)

        t_servo2 = Label(self.root,text='Hand',bg='white')
        t_servo2.place(x=430,y=200)

	t_depth = Label(self.root,text='Depth',bg='white')
	t_depth.place(x=250,y=85)

        t_cputemp = Label(self.root,text='CPU Temperature:',bg='white')
	t_cputemp.place(x=770,y=100)
	
	t_cputemp_num = Label(self.root,textvariable = cpu_temp_str,bg='white')
	t_cputemp_num.place(x=920,y=100)

	t_watertemp = Label(self.root,text='Water Temperature:',bg='white')
	t_watertemp.place(x=770,y=130)

	t_watertemp_num = Label(self.root,textvariable = water_temp_str,bg='white')
	t_watertemp_num.place(x=920,y=130)

	t_cabin_temp = Label(self.root,text='Cabin Temperature:',bg='white')
	t_cabin_temp.place(x=770,y=160)

	t_cabin_temp_num = Label(self.root,textvariable = cabin_temp_str,bg='white')
	t_cabin_temp_num.place(x=920,y=160)
	
        t_humidity = Label(self.root,text='Relative Humidity:',bg='white')
        t_humidity.place(x=770,y=190)

        t_humidity_num = Label(self.root,textvariable = humidity_str,bg='white')
        t_humidity_num.place(x=920,y=190)

	t_RAMused = Label(self.root,text='RAM Used:',bg='white')
	t_RAMused.place(x=770,y=220)

	t_RAMused_num = Label(self.root,textvariable = RAM_used_str,bg='white')
	t_RAMused_num.place(x=920,y=220)

	t_RAMfree = Label(self.root,text='RAM Free:',bg='white')
	t_RAMfree.place(x=770,y=250)

	t_RAMfree_num = Label(self.root,textvariable = RAM_free_str,bg='white')
	t_RAMfree_num.place(x=920,y=250)	
	
	t_Yaw = Label(self.root,text='Yaw:',bg='white')
	t_Yaw.place(x=50,y=380)

	t_Yaw_num = Label(self.root,textvariable = yaw_str,bg='white')
	t_Yaw_num.place(x=90,y=380)

	t_Roll = Label(self.root,text='Roll:',bg='white')
	t_Roll.place(x=180,y=380)

	t_Roll_num = Label(self.root,textvariable = roll_str,bg='white')
	t_Roll_num.place(x=220,y=380)

	t_Pitch = Label(self.root,text='Pitch:',bg='white')
	t_Pitch.place(x=360,y=380)

	t_Pitch_num = Label(self.root,textvariable = pitch_str,bg='white')
	t_Pitch_num.place(x=410,y=380)

	t_trajectory_display = Label(self.root,text='Trajectory Display',bg='white')
	t_trajectory_display.place(x=600,y=300)

	self.oval = Canvas(self.root,width=200,height=200,bg='white',highlightthickness=0)
        self.oval.place(x=50,y=70)
        self.background = self.oval.create_oval(0,0,200,200,fill="white")
	self.ball = self.oval.create_oval(70,70,130,130,fill="blue")
    
	self.yaw_canvas = Canvas(width=200,height=180,bg='white',highlightthickness=0)
	self.yaw_canvas.place(x=0,y=450)
	
	self.roll_canvas = Canvas(width=200,height=180,bg='white',highlightthickness=0)
	self.roll_canvas.place(x=180,y=450)

	self.pitch_canvas = Canvas(width=200,height=180,bg='white',highlightthickness=0)
	self.pitch_canvas.place(x=360,y=450) 
 	
	self.trace_canvas = Canvas(width=350,height=350,bg='gray',highlightthickness=3)
	self.trace_canvas.place(x=600,y=330)

	b_1 = Button(self.root,text='Zero',command=yaw_zero)
	b_1.place(x=120,y=290)
	
	b_2 = Button(self.root,textvariable=reverse_control_str,command=reverse_control)
	b_2.place(x=200,y=290)

	b_3 = Button(self.root,textvariable=start_stop_str,command=start_stop_control)
	b_3.place(x=50,y=290) 
 
    	b_4 = Button(self.root,text='Clear Trajectory',command=clear_trajectory)
	b_4.place(x=600,y=330)

	b_5 = Button(self.root,text='Zoom In',command=zoom_in)
	b_5.place(x=723,y=330)

	b_6 = Button(self.root,text='Zoom out',command=zoom_out)
	b_6.place(x=803,y=330)

    def GUI_update_temperature(self,GUI):
	self.temperature = get_cpu_temperature()
	cpu_temp_str.set(self.temperature)
	root.after(500,lambda:GUI.GUI_update_temperature(GUI))

    def GUI_update_RAM(self,GUI):
	RAM_stats = getRAMinfo()
	self.RAM_used = str(round(int(RAM_stats[1])/1000,1))+'MB'
	self.RAM_free = str(round(int(RAM_stats[2])/1000,1))+'MB'
	RAM_used_str.set(self.RAM_used)
	RAM_free_str.set(self.RAM_free)
	root.after(500,lambda:GUI.GUI_update_RAM(GUI))

    def GUI_update_water_temp(self,GUI):
	global water_temperature
	water_temp_str.set(str(water_temperature)+'˚C')
	root.after(500,lambda:GUI.GUI_update_water_temp(GUI))
 
    def GUI_update_humidity_temperature(self,GUI):
	global ht_select
	result = get_humidity_temperature()
	if ht_select == 0:
	    humidity_str.set(str(result)+'%')
	    ht_select = 1
	else:
	    cabin_temp_str.set(str(result)+'˚C')
	    ht_select = 0
	root.after(1000,lambda:GUI.GUI_update_humidity_temperature(GUI))

    def GUI_rotate_img(self,GUI,yawangle,rollangle,pitchangle):
	yawangle = -yawangle
	rollangle = -rollangle
	pitchangle = -pitchangle
	self.yawimage = Image.open("yawimg.gif")
	self.yawimg = ImageTk.PhotoImage(self.yawimage.rotate(yawangle))
	canvas_obj_yaw = self.yaw_canvas.create_image(100,90,
	image=self.yawimg)
	self.rollimage = Image.open("rollimg.gif")
	self.rollimg = ImageTk.PhotoImage(self.rollimage.rotate(rollangle))
	canvas_obj_roll = self.roll_canvas.create_image(100,90,
	image=self.rollimg)
	self.pitchimage = Image.open("pitchimg.gif")
	self.pitchimg = ImageTk.PhotoImage(self.pitchimage.rotate(pitchangle))
	canvas_obj_pitch = self.pitch_canvas.create_image(100,90,
	image=self.pitchimg)
	root.after(100,lambda:GUI.GUI_rotate_img(GUI,AUV_yaw,AUV_roll,AUV_pitch))

    def GUI_draw_trajectory(self,GUI,yawangle,distance,cnt):
	global x_0,y_0,isTrajectoryClear,zoom
	if isTrajectoryClear == 1:
	    self.trace_canvas.delete("all")
	    x_0 = 175
	    y_0 = 175
        isTrajectoryClear = 0
	x_1 = -zoom*distance*math.cos(radians(-yawangle-90))+x_0
	y_1 = zoom*distance*math.sin(radians(-yawangle-90))+y_0
	self.trace_canvas.create_line(x_0,y_0,x_1,y_1,
				      width = 4)
	x_0 = x_1
	y_0 = y_1

    def GUI_draw_ball(self,mouse_x,mouse_y):
	self.oval.delete("all")
	self.length = math.sqrt(math.pow((mouse_x-100),2)+math.pow((mouse_y-100)^2,2))
	if mouse_x != 0:
	    self.theta = math.atan2(mouse_x-100,100-mouse_y)*180/math.pi
	else:
	    self.theta = 0
	if self.length > 70:
	    k = 70/self.length
	    mouse_x = k*(mouse_x-100)+100
	    mouse_y = k*(mouse_y-100)+100
	self.oval_zero_x = mouse_x
	self.oval_zero_y = mouse_y
	self.oval_r = 30
	self.background = self.oval.create_oval(0,0,200,200,fill="white")
	self.ball = self.oval.create_oval(self.oval_zero_x - self.oval_r,
					  self.oval_zero_y - self.oval_r,
					  self.oval_zero_x + self.oval_r,
					  self.oval_zero_y + self.oval_r,fill="blue")

    def motion(self,event):
	x = event.x
	y = event.y
	self.GUI_draw_ball(x,y)

def main():
    try:
        GUI = consoleGUI(root)
	GUI.oval.bind('<B1-Motion>',GUI.motion)
        root.after(500,lambda:send_values(root,GUI))
	root.after(500,select_humidity_temperature)
	root.after(500,lambda:GUI.GUI_update_temperature(GUI))
	root.after(500,lambda:GUI.GUI_update_RAM(GUI))
	root.after(500,lambda:GUI.GUI_update_water_temp(GUI))
	root.after(1000,lambda:GUI.GUI_update_humidity_temperature(GUI))
	root.after(100,lambda:GUI.GUI_rotate_img(GUI,AUV_yaw,AUV_roll,AUV_pitch))
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()
        print "done!"

if __name__ == "__main__":
    main()

