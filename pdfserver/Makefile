jquery_path=http://code.jquery.com/jquery-1.4.2.min.js
jquery-ui_path=http://jqueryui.com/download/jquery-ui-1.8.4.custom.zip
jquery-validate_path=http://ajax.microsoft.com/ajax/jquery.validate/1.7/jquery.validate.min.js

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

tmp/jquery.validate.min.js:
	mkdir -p tmp
	cd tmp && wget ${jquery-validate_path}

jquery-validate: tmp/jquery.validate.min.js
	mkdir -p tmp/media/js
	cp tmp/jquery.validate.min.js tmp/media/js/jquery.validate.min.js

deploy: jquery jquery-ui jquery-validate
	mkdir -p media/css
	mkdir -p media/js
	mv tmp/media/css/* media/css
	mv tmp/media/js/* media/js

clean:
	rm -r tmp/
