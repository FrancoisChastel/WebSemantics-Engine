# How to setup Web project 

First, install dependencies using bower in the web directory :
```shell
cd web
bower install
```
A folder named 'assets' must have been created.

Open the file 
```html
web/index.html
```

Then, run the flask server which will intercepet AJAX requests from the view. You have to cd the directory core/sel-app/server and type 
```shell
export FLASK_APP=server.py
```

You can now search whatever you want
