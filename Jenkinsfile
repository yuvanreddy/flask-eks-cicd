pipeline {
  agent any

  environment {
    AWS_REGION         = "us-east-1"
    CLUSTER_NAME       = "flask-eks"
    AWS_ACCOUNT_ID     = "816069153839"
    ECR_REPO           = "myrepo_flask"
    IMAGE_TAG          = "${BUILD_NUMBER}"
    ECR_URI            = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
    KUBECONFIG         = "/var/lib/jenkins/.kube/config"
    PATH               = "/usr/local/bin:/usr/bin:/bin"
    AWS_DEFAULT_REGION = "us-east-1"

    WEBHOOK_URL        = "https://hooks.slack.com/services/XXXX/XXXX/XXXX"
    INGRESS_NAME       = "flask-ingress"
    NAMESPACE          = "default"
  }

  stages {

    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/yuvanreddy/flask-eks-cicd.git'
      }
    }

    stage('Build Image') {
      steps {
        sh '''
          docker build -t ${ECR_REPO}:${IMAGE_TAG} app/
        '''
      }
    }

    stage('Login to ECR') {
      steps {
        sh '''
          aws ecr get-login-password --region ${AWS_REGION} | \
            docker login --username AWS --password-stdin \
            ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
        '''
      }
    }

    stage('Push Image') {
      steps {
        sh '''
          docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
          docker push ${ECR_URI}:${IMAGE_TAG}
        '''
      }
    }

    stage('Update kubeconfig') {
      steps {
        sh '''
          aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
          kubectl config current-context
        '''
      }
    }

    stage('Deploy to EKS') {
      steps {
        sh '''
          # Render deployment yaml without modifying original
          sed "s|IMAGE_TAG|${IMAGE_TAG}|g" k8s/deployment.yaml > k8s/deployment_rendered.yaml

          kubectl apply -f k8s/deployment_rendered.yaml --validate=false
          kubectl apply -f k8s/service.yaml --validate=false
          kubectl apply -f k8s/ingress.yaml --validate=false

          kubectl rollout status deployment/flask-app --timeout=180s
        '''
      }
    }

    stage('Verify + Print ALB URL') {
      steps {
        sh '''
          echo "=== PODS ==="
          kubectl get pods -n ${NAMESPACE} -o wide

          echo "=== INGRESS ==="
          kubectl get ingress -n ${NAMESPACE}

          echo "Waiting for ALB URL..."
          for i in {1..30}; do
            URL=$(kubectl get ingress ${INGRESS_NAME} -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
            if [ ! -z "$URL" ]; then
              echo "✅ Flask App URL: http://$URL"
              echo "$URL" > alb_url.txt
              exit 0
            fi
            sleep 10
          done

          echo "❌ ALB URL not assigned yet. Check ingress:"
          kubectl describe ingress ${INGRESS_NAME} -n ${NAMESPACE}
        '''
      }
    }

    stage('Webhook Notify') {
      steps {
        script {
          def url = "Not Assigned"
          if (fileExists('alb_url.txt')) {
            url = sh(script: "cat alb_url.txt", returnStdout: true).trim()
          }

          sh """
            curl -X POST -H 'Content-type: application/json' \
            --data '{
              "text": "✅ Jenkins Deployment SUCCESS\\nJob: ${JOB_NAME}\\nBuild: #${BUILD_NUMBER}\\nECR Image: ${ECR_URI}:${IMAGE_TAG}\\nApp URL: http://${url}"
            }' ${WEBHOOK_URL}
          """
        }
      }
    }
  }

  post {
    failure {
      sh """
        curl -X POST -H 'Content-type: application/json' \
        --data '{
          "text": "❌ Jenkins Deployment FAILED\\nJob: ${JOB_NAME}\\nBuild: #${BUILD_NUMBER}\\nCheck Jenkins console logs."
        }' ${WEBHOOK_URL}
      """
    }
  }
}
