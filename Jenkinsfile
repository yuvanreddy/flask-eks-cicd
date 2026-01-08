pipeline {
  agent any

  environment {
    AWS_REGION = "ap-south-1"
    ECR_REPO   = "flask-eks"
    IMAGE_TAG  = "${BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps { git 'https://github.com/your-org/flask-eks-cicd.git' }
    }

    stage('Build Image') {
      steps {
        sh "docker build -t $ECR_REPO:$IMAGE_TAG app/"
      }
    }

    stage('Push to ECR') {
      steps {
        sh """
        aws ecr get-login-password --region $AWS_REGION |
        docker login --username AWS --password-stdin <AWS_ACCOUNT>.dkr.ecr.$AWS_REGION.amazonaws.com
        docker tag $ECR_REPO:$IMAGE_TAG <AWS_ACCOUNT>.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
        docker push <AWS_ACCOUNT>.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
        """
      }
    }

    stage('Deploy to EKS') {
      steps {
        sh """
        sed -i 's|ECR_IMAGE|<AWS_ACCOUNT>.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO|g' k8s/deployment.yaml
        sed -i 's|IMAGE_TAG|$IMAGE_TAG|g' k8s/deployment.yaml
        kubectl apply -f k8s/
        """
      }
    }
  }
}
