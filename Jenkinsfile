pipeline {
  agent any

  environment {
    AWS_REGION = "us-east-1"
    CLUSTER_NAME = "flask-eks"
    AWS_ACCOUNT_ID = "816069153839"
    ECR_REPO = "myrepo_flask"
    IMAGE_TAG = "${BUILD_NUMBER}"
    ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
    KUBECONFIG = "/var/lib/jenkins/.kube/config"
    PATH = "/usr/local/bin:/usr/bin:/bin"
  }

  stages {

    stage('Checkout') {
      steps { git branch: 'main', url: 'https://github.com/yuvanreddy/flask-eks-cicd.git' }
    }

    stage('Build Image') {
      steps { sh 'docker build -t ${ECR_REPO}:${IMAGE_TAG} app/' }
    }

    stage('Login to ECR') {
      steps {
        sh '''
          aws ecr get-login-password --region ${AWS_REGION} |
          docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
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

    stage('Configure Kubeconfig') {
      steps {
        sh '''
          aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
        '''
      }
    }

    stage('Configure RBAC aws-auth') {
      steps {
        sh '''
          kubectl apply -f k8s/aws-auth.yaml --validate=false
        '''
      }
    }

    stage('Deploy to EKS') {
      steps {
        sh '''
          sed -i "s|IMAGE_TAG|${IMAGE_TAG}|g" k8s/deployment.yaml
          kubectl apply -f k8s/ --validate=false
        '''
      }
    }

    stage('Print App URL') {
      steps {
        sh '''
          echo "Waiting for LoadBalancer..."
          kubectl get svc flask-service
          echo "App URL:"
          kubectl get svc flask-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
          echo ""
        '''
      }
    }
  }
}
