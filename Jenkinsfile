pipeline {
    agent {
    docker { image 'python:2.7.16-stretch' }
    }
    stages {
        stage('build') {
            steps {
                sh 'python --version'
            }
        }
    }
}
