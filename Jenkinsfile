pipeline {
  agent any

  environment {
    AWS_REGION = "us-east-1"
    AWS_ACCOUNT_ID = "816069153839"
    ECR_REPO = "myrepo_flask"
    IMAGE_TAG = "${BUILD_NUMBER}"
    ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
  }

  stages {

    stage('Checkout') {
      steps {
        git 'https://github.com/your-org/flask-eks-cicd.git'
      }
    }

    stage('Build Docker Image') {
      steps {
        sh """
          docker build -t ${ECR_REPO}:${IMAGE_TAG} app/
        """
      }
    }

    stage('Login to ECR') {
      steps {
        sh """
          aws ecr get-login-password --region ${AWS_REGION} |
          docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
        """
      }
    }

    stage('Tag & Push Image') {
      steps {
        sh """
          docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
          docker push ${ECR_URI}:${IMAGE_TAG}
        """
      }
    }

    stage('Deploy to EKS') {
      steps {
        sh """
          sed -i 's|IMAGE_TAG|${IMAGE_TAG}|g' k8s/deployment.yaml
          kubectl apply -f k8s/
        """
      }
    }
  }
}
