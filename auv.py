# coding=UTF-8
from Tkinter import *
from PIL import Image,ImageTk
import threading
import math
import serial
import os

root = Tk()
cpu_temp_str = StringVar()
RAM_used_str = StringVar()
RAM_free_str = StringVar()
ser = serial.Serial("/dev/ttyAMA0",115200,timeout=0.1)
isZeroSet = 0
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

def yaw_zero():
    global isZeroSet
    isZeroSet = 1    

def com_data_convert(data):
    if data < 10:
	str_data = '00'+str(data)
    if data >= 10 and data < 100:
	str_data = '0'+str(data)
    if data > 100:
	str_data = str(data)
    return str_data

def fetch_values():
    #try:
    #    s = ser.readlines()
    #except:
    #    pass
    #if len(s) > 0:
    #    data = s[0].split('A')
    #    info = data[1].split('x')
    #    print info
    root.after(100,fetch_values)
     
def send_values(root,GUI):
    global isZeroSet
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
    package = 'A'+yaw_str+'x'+speed_str+'x'+depth_str+'x'+servo_1_str+'x'+servo_2_str+'x'+isZeroSet_str
    isZeroSet = 0
    ser.write(package)
    print package
    root.after(500,lambda:send_values(root,GUI))

class consoleGUI:
    def __init__(self,root):
        self.root = root

        self.root.geometry("800x600+0+0")
	self.length = 0
	self.theta = 0
        t_name = Label(self.root,text='AUV Console',font=('Arial',15))
	t_name.pack()

        t_ouc = Label(self.root,text='Ocean University of China',
        font=('Arial',10))
        t_ouc.place(x=320,y=40)

        self.w1 = Scale(self.root, from_=0, to=30, length=200, tickinterval=4)
        self.w1.set(0)
        self.w1.place(x=350,y=80)

	self.servo1 = Scale(self.root, from_=0, to=100, length=270, tickinterval=10, orient=HORIZONTAL)
        self.servo1.set(0)
        self.servo1.place(x=480,y=120)

	t_servo1 = Label(self.root,text='Arm')
	t_servo1.place(x=480,y=100)

	self.servo2 = Scale(self.root, from_=0, to=100, length=270, tickinterval=10, orient=HORIZONTAL)
        self.servo2.set(0)
        self.servo2.place(x=480,y=220)

        t_servo2 = Label(self.root,text='Hand')
        t_servo2.place(x=480,y=200)

	t_depth = Label(self.root,text='depth')
	t_depth.place(x=300,y=85)

        t_cputemp = Label(self.root,text='CPU Temperature:')
	t_cputemp.place(x=80,y=350)
	
	t_cputemp_num = Label(self.root,textvariable = cpu_temp_str)
	t_cputemp_num.place(x=200,y=350)

	t_RAMused = Label(self.root,text='RAM Used:')
	t_RAMused.place(x=300,y=350)

	t_RAMused_num = Label(self.root,textvariable = RAM_used_str)
	t_RAMused_num.place(x=370,y=350)

	t_RAMfree = Label(self.root,text='RAM Free:')
	t_RAMfree.place(x=500,y=350)
	
	t_RAMfree_num = Label(self.root,textvariable = RAM_free_str)
	t_RAMfree_num.place(x=570,y=350)	
	
	self.oval = Canvas(self.root,width=200,height=200)
        self.oval.place(x=100,y=70)
        self.background = self.oval.create_oval(0,0,200,200,fill="white")
	self.ball = self.oval.create_oval(70,70,130,130,fill="blue")
    
	self.canvas = Canvas(width=180,height=180)
	self.canvas.place(x=100,y=420) 
 	
	b = Button(self.root,text='Zero',command=yaw_zero)
	b.place(x=170,y=290)
  
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

    def GUI_rotate_img(self,GUI,angle):
	angle = -angle
	self.image = Image.open("auv.GIF")
	self.img = ImageTk.PhotoImage(self.image.rotate(angle))
	canvas_obj = self.canvas.create_image(90,90,
	image=self.img)
	root.after(100,lambda:GUI.GUI_rotate_img(GUI,GUI.theta))

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
	root.after(100,fetch_values)
	root.after(500,lambda:GUI.GUI_update_temperature(GUI))
	root.after(500,lambda:GUI.GUI_update_RAM(GUI))
	root.after(100,lambda:GUI.GUI_rotate_img(GUI,GUI.theta))
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()
        print "done!"

if __name__ == "__main__":
    main()

