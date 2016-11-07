# How to setup Symfony project 

First, go into IHM folder with the command line and execute 
’’’shell
php composer.phar install
’’’

Then, execute 
’’’shell
bower install
’’’

Then, run 
’’’shell
php bin/symfony_requirements
’’’
Check the results, if it is all green, you can step to the next step

Then, run 
’’’shell
php bin/console doctrine:database:create
’’’

Then, set a new VirtualHost which leads to the 'web' folder into the IHM folder

You can now access with your preferred browser to the project by typing the name of the VHost you just created :
’’’html
http://host/app_dev.php
’’’  

Enjoy

# How to use engine.sh

./engine.sh [your request]

You need to get an custom search API, key with your google account on https://console.developers.google.com/apis/.
And to instanciate a search engine on your account's control panel. 

# API keys
! Careful : there is a request limit per day on certain API. If you want to debug something that required a lof of request, you shall get your own key.

Antoine Breton api keys :
 - Google Custom Search : AIzaSyB55Q4tpXmOmXrRaYU2MC7IvfGRn-VQa6c
 - 

Nathan Haim api keys :
 - Google Custom Search : AIzaSyDD_G35f_j1hmzNMdLESHWsliwYVbjP2BA
