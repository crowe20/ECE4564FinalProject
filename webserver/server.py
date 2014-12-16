__author__ = 'Robert'
from twisted.web import server, static
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
import time
import os

# http://twistedmatrix.com/documents/current/web/howto/web-in-60/dynamic-content.html

base_path = "files"
host_ip = "localhost"
node_list = None

test_host = "rtsp://192.168.1.59:"
test_port = "25701"
test_file = "/stream25701.h264"



def updateGlobalVars():
    file = open("config.txt","r")
    global base_path
    global host_ip
    host_ip = file.readline().split(":")[1].strip()
    base_path = file.readline().strip()
    file.close()
    getNodeList()
    return base_path

def getNodeList():
    print "Getting node list"
    global node_list
    node_list =  os.listdir(base_path+"nodes/")
    print "Done"

def getPort(fileName):
    return "25700"

def getArchiveList(path):
    return ""

class ClockPage(Resource):
    isLeaf = True
    def render_GET(self, request):
        print request.uri
        return "<html><body>%s</body></html>" % (time.ctime(),)

class ImgPage(Resource):
    isLeaf = True
    def render_GET(self, request):
        print base_path+request.uri
        #find image
        image = "files/cat1.jpg"
        return '<html><body>Image Page<br/><img src="/%s"/></body></html>' % (image,)

class FileListPage(Resource):
    isLeaf = True
    def render_GET(self, request):
        body = ""
        for file in os.listdir(base_path+request.uri):
            if not request.uri.endswith("/"):
                request.uri+="/"
            pageName = file
            if file.endswith(".jpg"):
                pageName= "ImagePage/" + file
            body+= "<a href="+request.uri+pageName+">"+file+ "</a><br/>"
        body+= '<a href="clock">clock</a><br/>'
        body+= '<a href="/">home</a><br/>'

        old =  '<html><body>Index Page<br/>%s' % (body,)
        old += '<embed type="application/x-vlc-plugin" name="VLC" autoplay="yes" loop="no" volume="100" width="640" height="480" target="'+test_host+test_port+test_file+'"/>' \
                '</body></html>'

        return old

class HomePage(Resource):
    isLeaf = True
    def render_GET(self, request):
        body = ""
        getNodeList()
        for file in node_list:
            body+= "<a href="+request.uri+file+">"+file+ "</a><br/>"

        page =  '<html><body>Index Page<br/>%s' % (body,)
        #old += '<embed type="application/x-vlc-plugin" name="VLC" autoplay="yes" loop="no" volume="100" width="640" height="480" target="'+test_host+test_port+test_file+'"/>' \
        page += '</body></html>'

        return page

class NodePage(Resource):
    isLeaf = True
    def render_GET(self, request):
        name = request.uri[1:]
        table = '<table width="100%%" height="100%%" border="1"><th colspan="3">%s</th>' \
                '<tr align="center"><td>Archived Videos</td><td>Live Stream</td><td>Log Output</td></tr><tr>'\
                '<td width="25%%">%s</td>' \
                '<td width="50%%" align="center">%s</td>' \
                '<td width="25%%">%s</td>' \
                '</tr><th colspan="3"><a href="/">Home</a></th></table>'

        archiveList = ""
        for file in os.listdir(base_path+"nodes"+request.uri+"/archive/"):
            archiveList += '<a href="'+name+"/"+file.split(".")[0]+'">'+file+'</a><br/>'

        streamFileDir = base_path + "nodes/" + name + "/current/"
        videoContent = ""
        try:
            streamFile = ""
            for fileName in os.listdir(streamFileDir):
                if "stream" in fileName:
                    streamFile = fileName
            portIndex = streamFile.index("257")
            port = streamFile[portIndex:portIndex+5]
            videoContent = '<embed type="application/x-vlc-plugin" name="VLC" autoplay="yes" loop="no" volume="100" width="100%%" height="100%%" target="'+"rtsp://"+host_ip+":"+port+"/"+streamFile+'"/>'
        except:
            videoContent = "Live Stream Not Available: Try Again Later <br/>"
            print "Failed to get livestream"


        body =  '<html><body>'
        body += table % (name, archiveList, videoContent, "log",)
        body += '</body></html>'
        return body

class NodeArchivePage(Resource):
    isLeaf = True
    def render_GET(self, request):
        name, video = request.uri[1:].split("/")
        body = ""
        body += '<a href="/">home</a><br/>'
        body += "Archived Video: "+video+"<br/>"
        body+= '<a href=/'+name+'>Node Home</a><br/>'

        old =  '<html><body>Node: %s<br/>%s' % (name, body, )
        #old += '<embed type="application/x-vlc-plugin" name="VLC" autoplay="yes" loop="no" volume="100" width="640" height="480" target="'+test_host+test_port+test_file+'"/>' \
        old+=        '</body></html>'
        print "NodePage done"
        return old

class BasePage(Resource):
    isLeaf = True
    def render_GET(self, request):
        print request.uri
        if request.uri == "/":
            print "HomePage"
            return HomePage().render_GET(request)
        elif request.uri[1:] in node_list:
            print "NodePage"
            return NodePage().render_GET(request)
        elif request.uri[1:].split("/")[0] in node_list:
            print "NodeArchivePage"
            return NodeArchivePage().render_GET(request)
        elif os.path.isdir(base_path+request.uri):
            print "FileListPage"
            return FileListPage().render_GET(request)
        elif "ImagePage/" in request.uri:
            print "ImgPage"
            return ImgPage().render_GET(request)
        elif request.uri == "/clock":
            print "ClockPage"
            return ClockPage().render_GET(request)
        else:
            print "FilePage"
            print request.uri
            return static.File("files/test3.ogg").render_GET(request)

def server_main():
    updateGlobalVars()
    getNodeList()
    resource = BasePage()
    resource.putChild("files", static.File("files"))
    factory = Site(resource)
    reactor.listenTCP(8080, factory)
    reactor.run()


server_main()
