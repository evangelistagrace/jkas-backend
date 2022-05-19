node{
    stage('cloning git'){
        git branch:'dev',credentialsId:'github', url:"https://github.com/1centroxy/jkas_backend_python.git"
    }
    stage('build') {
        sh   'echo $USER'
    
        sh   'apt-get -y install python3-pip'
        sh   'apt-get -y install unixodbc-dev'
        sh   'pip install --upgrade pip'
        
        
        sh   'python3 -m pip install virtualenv'
        sh   'python3 -m virtualenv venv'
        
        sh """
        . venv/bin/activate
        pip install -r requirements.txt
        """
    }
        stage('deploy') {
        sh """
        . venv/bin/activate
        systemctl enable jkas
        """
        sh """
        . venv/bin/activate
        systemctl stop jkas
        """
        sh """
        . venv/bin/activate
        systemctl start jkas
        """
    }
    stage('Notify') {
        office365ConnectorSend message: 'Jkas_Deploy_Done', status: 'Success', webhookUrl: 'https://centroxyweb.webhook.office.com/webhookb2/e11133d2-c97f-4d7f-bf34-1ca56031ec52@094737d4-5bce-418d-89e0-0ee3815f1ad7/JenkinsCI/c2127c5865eb41b9a6f7e0d9870f2745/dd98fbd0-9e02-44d6-b50e-05b13dfa2c8f'
    }
   
}
