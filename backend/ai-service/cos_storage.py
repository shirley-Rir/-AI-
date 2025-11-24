
import os
import base64
import uuid
from datetime import datetime
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class COSStorage:
    """腾讯云COS存储工具类"""

    def __init__(self):
        # 初始化COS配置
        self.secret_id = os.getenv('COS_SECRET_ID')
        self.secret_key = os.getenv('COS_SECRET_KEY')
        self.region = os.getenv('COS_REGION', 'ap-guangzhou')
        self.bucket_name = os.getenv('COS_BUCKET_NAME')
        self.bucket_domain = os.getenv('COS_BUCKET_DOMAIN')
        self.base_path = os.getenv('COS_BASE_PATH', 'uploads')

        if not all([self.secret_id, self.secret_key, self.bucket_name]):
            raise ValueError("COS配置不完整，请检查环境变量")

        # 初始化COS客户端
        config = CosConfig(
            Region=self.region,
            SecretId=self.secret_id,
            SecretKey=self.secret_key
        )
        self.client = CosS3Client(config)

    def upload_base64_image(self, base64_data, folder="history_images"):
        """
        将base64编码的图片上传到COS

        Args:
            base64_data: base64编码的图片数据
            folder: COS存储文件夹名称

        Returns:
            图片的URL地址，如果上传失败则返回None
        """
        try:
            # 去除base64数据的前缀（如果有）
            if 'base64,' in base64_data:
                base64_data = base64_data.split('base64,')[1]

            # 解码base64数据
            image_data = base64.b64decode(base64_data)

            # 生成唯一的文件名
            file_extension = 'jpg'  # 默认使用jpg扩展名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"{timestamp}_{unique_id}.{file_extension}"

            # 上传到COS，使用配置的基础路径
            object_key = f"{self.base_path}/{folder}/{file_name}"
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Body=image_data,
                Key=object_key,
                ContentType='image/jpeg'
            )

            # 检查上传是否成功
            # 有些情况下，响应可能不包含'Response'键，但包含'ETag'键
            etag = None
            if 'Response' in response and response['Response'].get('ETag'):
                etag = response['Response'].get('ETag')
            elif response.get('ETag'):
                etag = response.get('ETag')

            if etag:
                # 返回完整的图片URL
                return f"https://{self.bucket_name}.cos.{self.region}.myqcloud.com/{object_key}"
            else:
                print(f"COS上传失败: {response}")
                return None

        except Exception as e:
            print(f"上传图片到COS出错: {str(e)}")
            return None

    def delete_image(self, image_url):
        """
        从COS删除图片

        Args:
            image_url: 图片的URL地址

        Returns:
            删除是否成功
        """
        try:
            # 从URL中提取object key
            if f"{self.bucket_name}.cos.{self.region}.myqcloud.com/" in image_url:
                object_key = image_url.split(f"{self.bucket_name}.cos.{self.region}.myqcloud.com/")[1]
            else:
                print(f"无法从URL中提取COS对象key: {image_url}")
                return False

            # 从COS删除对象
            response = self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            # 检查删除是否成功
            # 有些情况下，响应可能不包含'Response'键
            status_code = None
            if 'Response' in response and response['Response'].get('statusCode'):
                status_code = response['Response'].get('statusCode')
            # 对于删除操作，如果没有错误，通常认为操作成功
            elif 'statusCode' not in response and 'code' not in response:
                # 没有错误码，认为操作成功
                return True

            if status_code == 204:
                return True
            else:
                print(f"COS删除失败: {response}")
                return False

        except Exception as e:
            print(f"从COS删除图片出错: {str(e)}")
            return False
