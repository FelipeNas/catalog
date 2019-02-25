# Item Catalog

This project is part of the [UDACITY Full-Stack ND](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

The objective was to make a restful web application using Python framework Flask, third-party Oauth authentication and CRUD.

## Prerequisites

Clone the repository and download:

[Git Bash](https://git-scm.com/downloads) for windows  
[Virtual Box 5.1](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)  
[Vagrant](https://www.vagrantup.com/downloads.html)

Install Git Bash for windows;  
Install Virtual Box 5.1;  
Install Vagrant

Through the terminal cd into the **catalog** directory  
Inside the directory **catalog**, type: `vagrant up`.  
Wait until `vagrant up` is finish running.  
Now type: `vagrant ssh` to log in the VM.
```
$ cd /LogAnalisys
$ vagrant up
...
$ vagrant ssh
```

Logged into the VM cd into the vagrant directory: `cd /vagrant`



## How to use

Logged into the VM  
Inside the directory **vagrant**  
Run `python application.py`  
Visit http://localhost:8000/


## API

The structure of the JSON API

    {
      "Restaurants": [
        {
          "id": 1,
          "name": "Restaurant Example"
        },
        {
          "id": 2,
          "name": "Restaurant Example 2"
        }
      ]
    }
