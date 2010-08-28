jquery_path=http://code.jquery.com/jquery-1.4.2.min.js
jquery-ui_path=http://jqueryui.com/download/jquery-ui-1.8.4.custom.zip

tmp/jquery.js:
	mkdir -p tmp
	cd tmp && wget ${jquery_path} -O jquery.js

jquery: tmp/jquery.js
	mkdir -p tmp/media/js
	cp tmp/jquery.js tmp/media/js/

tmp/jquery-ui.zip:
	mkdir -p tmp
	cd tmp && wget ${jquery-ui_path} -O jquery-ui.zip
	unzip tmp/jquery-ui.zip -d tmp/jquery-ui

jquery-ui: tmp/jquery-ui.zip
	mkdir -p tmp/media/css
	mkdir -p tmp/media/css/images
	mkdir -p tmp/media/js
	cp tmp/jquery-ui/js/jquery-ui*.js tmp/media/js/jquery-ui.js
	cp tmp/jquery-ui/css/smoothness/jquery-ui*.css tmp/media/css/jquery-ui.css
	cp tmp/jquery-ui/css/smoothness/images/* tmp/media/css/images

deploy: jquery jquery-ui
	mkdir -p media
	mv tmp/media/css media/
	mv tmp/media/js media/

clean:
	rm -r tmp/
