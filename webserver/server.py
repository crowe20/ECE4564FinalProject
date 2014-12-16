__author__ = 'Robert'
from twisted.web import server, static
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
import time
import os

# http://twistedmatrix.com/documents/current/web/howto/web-in-60/dynamic-content.html

base_path = "files"

test_host = "rtsp://192.168.1.59:"
test_port = "25701"
test_file = "/stream25701.h264"

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

class BasePage(Resource):
    isLeaf = True
    def render_GET(self, request):
        print request.uri
        if os.path.isdir(base_path+request.uri):
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
    resource = BasePage()
    resource.putChild("files", static.File("files"))
    factory = Site(resource)
    reactor.listenTCP(8080, factory)
    reactor.run()


server_main()
