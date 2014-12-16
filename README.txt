Team Observer
REMOTE SECURITY SYSTEM

To Run:
have version of python 2.7.3
	running on a different version of python may cause problems
Please install the following libraries
	pika
	twisted
	picamera (maybe pre-installed) 
	
To setup the security system:
	connect raspberry pi camera board (from element 14) to the camera bus
	connect the motion sensor to the GPIO Pins
		red to power
		black to ground
		yellow io pin to raspberry pi GPIO pin
		reccomended to use external breadboard
	place the pi, cameras, and motion sensors around a local network

Configuring the system 
	config.txt:
	change the external IP field to the ip of the machine that will be hosting the server
	the local file directory that the path to store the video
	the non alerting times take '+' seperated bracketed lists of the time at which to not alert
		format: [day or week, 24 hr start time, 24 hr end time]
		these times can not span multiple days
		example: [monday, 9:00, 10:00] will not send alerts from 9:00AM to 10:00 AM on monday 
		example: [monday, 9:00, 10:00]+[tuesday,9:00,10:00] will not send alerts from 9:00AM to 10:00 AM on monday and tuesday 
	 any following lines will include email address and user name as a comma seperated values
		i.e. email addres, user name
		example: user@someEmail.com, userName
	
	security nodes:
	for each security node, the local ip and port needs to be updated for each network
	AMQP publish messages in healthReport.py and pollForMotion.py
 
Launch the server:
	to launch the webserver:
		in the direct the file server.py is located run: 
			python server.py
	to launch the security client:
		in the directory the file securityClient.py is located run:
			python securityClient.py
	The Server process launches access to the webserver
		to access, in a browser, go to the externalIP listed in the config.txt file:8080
		example: 1.2.3.4:8080
		the browser needs to have the vlc plugin allowed
			the plugin can be downloaded from videolan.org/vlc/index.html
	The securityClient process launches the processes that send email alerts and stream video
	These proceses must be launched first to see any activity

	on each security node:
		launch the command 'python videoStream.py &'
		then run crontab -e and add the following string to the bottom of the file
		"* * * * * python /path/to/file/healthReport.py"
		then exit  crontab (ctrl x, y)
		execute 'sudo python pollForMotion.py'
			this process takes 60 seconds to stabilize

YOUR SYSTEM SHOULD NOW BE RUNNING
	stream will be available approximately 30 seconds after the first health message is received 

	to exit:
		python server.py can be killed with ctrl c
		python securityClient.py can be killed with the following process
			ctrl z, ps, then 'kill -9 <the pid for python>'
		python pollForMotion can be killed with ctrl c
		crontab can be disabled by adding a '#' in front of the command
		python videoStream.py can be killed with
			ps, 'kill -9 <pid for python>'
	
