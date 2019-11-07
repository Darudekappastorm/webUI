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
    stage('analysis') {
            steps {
                script {
                    try {
                        sh '''
                        #!/bin/bash
                        find . -name \\*.py| grep -v test | grep -v \\.local | grep -v env | xargs python2 -m pylint --rcfile=.pylintrc --exit-zero --output-format=parseable --reports=y | tee pylint.log
                        '''
                    } catch(Exception e) {
                        echo "EXCEPTION: ${e}" 
                    } finally {
                        def pyLintIssues = scanForIssues tool: pyLint(pattern: 'pylint.log')
                        publishIssues id: 'pyLint', qualityGates: [[threshold: 1, type: 'TOTAL_ERROR', unstable: true], [threshold: 15, type: 'TOTAL_HIGH', unstable: true]], issues: [pyLintIssues], name: 'pyLint'
                    }
                }
            }
        }
}
