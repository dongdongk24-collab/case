# Tools

실제 일을 하는 파이썬 파일들.

## 원칙

- Tool 하나 = 하나의 역할만
- 예측 가능하고, 테스트 가능하게
- API 키는 절대 코드에 직접 쓰지 말고 `.env`에서 읽어올 것
- 새 Tool 만들기 전에 기존 Tool 먼저 확인

## 사용법

```python
# .env 읽는 기본 패턴
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")
```
