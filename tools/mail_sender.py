import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from utils import logger
from config import settings


class MailSender:
    """邮件发送工具，从环境变量读取SMTP配置"""
    def execute(self, to_addrs, subject, body, from_addr=None, body_type='plain'):
        """
        发送邮件
        :param to_addrs: 收件人，可以是单个邮箱字符串或邮箱列表
        :param subject:   邮件主题
        :param body:      邮件正文
        :param from_addr: 发件人地址，若为None则使用 SMTP_USER
        :param body_type: 正文类型，'plain' 或 'html'
        :return:          True 表示发送成功
        :raises ValueError: 配置缺失或发送失败时抛出异常
        """
        # ----- 1. 获取SMTP配置 -----
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        username = settings.SMTP_USER
        password = settings.SMTP_PASSWORD
        use_tls = settings.SMTP_USE_TLS
        from_name = settings.SMTP_FROM   # 发件人显示名称，可选

        # 必要配置校验
        if not all([smtp_host, smtp_port, username, password]):
            missing = []
            if not smtp_host: missing.append(self.ENV_SMTP_HOST)
            if not smtp_port: missing.append(self.ENV_SMTP_PORT)
            if not username: missing.append(self.ENV_SMTP_USER)
            if not password: missing.append(self.ENV_SMTP_PASSWORD)
            raise ValueError(f"缺少必要的SMTP环境变量: {', '.join(missing)}")

        # ----- 2. 构建邮件对象 -----
        # 处理收件人格式
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]
        to_str = ','.join(to_addrs)

        # 确定发件人地址
        if from_addr is None:
            from_addr = username

        # 创建邮件正文
        msg = MIMEText(body, body_type, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        # 发件人：可包含显示名称
        if from_name:
            msg['From'] = formataddr((Header(from_name, 'utf-8').encode(), from_addr))
        else:
            msg['From'] = from_addr
        msg['To'] = to_str

        # ----- 3. 发送邮件 -----
        try:
            logger.info(f"准备发送邮件，收件人: {to_str}, 主题: {subject}")
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)
            logger.info(f"邮件发送成功，收件人: {to_str}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            raise ValueError(f"邮件发送失败: {e}")