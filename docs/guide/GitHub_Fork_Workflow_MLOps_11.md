
# 🧭 GitHub Classroom: 개인 개발 흐름 (Fork → Clone → Push → PR)

> 🎯 목표: 조별 GitHub 레포에서 개인 계정으로 fork한 후, 로컬에서 작업 → push → PR을 통해 팀 레포에 기여
> 📝 레포 이름: `mlops-cloud-project-mlops_11` (개인 GitHub에서도 이 이름 유지)

---

## ✅ 1단계: 조 GitHub 레포를 개인 계정으로 Fork

🔗 예시 조 레포 주소:

```
https://github.com/roundielab-edu/mlops-cloud-project-mlops_11
```

### 👉 GitHub에서 할 일

1. 위 URL에 접속
2. 우측 상단의 `Fork` 버튼 클릭
3. **본인 개인 계정**으로 fork 선택
4. Fork 후, 레포 이름은 그대로 `mlops-cloud-project-mlops_11`으로 유지

---

## ✅ 2단계: 개인 계정의 Fork된 레포를 로컬로 Clone

### 🔍 예시 개인 계정의 fork 주소

```
https://github.com/yourusername/mlops-cloud-project-mlops_11.git
```

### 💻 로컬에 clone

```bash
git clone https://github.com/yourusername/mlops-cloud-project-mlops_11.git
cd mlops-cloud-project-mlops_11
```

---

## ✅ 3단계: 작업 파일 생성 또는 수정

예: 새 파일 추가 또는 기존 파일 수정

```bash
touch my_notebook.ipynb
echo "# 실험 노트북입니다." > my_notebook.ipynb
```

---

## ✅ 4단계: Git에 변경사항 저장 (add → commit → push)

```bash
git add my_notebook.ipynb
git commit -m "Add: 개인 실험 노트북 추가"
git push origin main
```

> `main`이 아닌 경우 `git branch` 명령으로 현재 브랜치 확인 후 push

---

## ✅ 5단계: 조 GitHub 레포에 PR(Pull Request) 생성

### GitHub 웹에서 할 일

1. 본인 레포로 이동: `https://github.com/yourusername/mlops-cloud-project-mlops_11`
2. 상단에 "Compare & pull request" 또는 "Pull request" 클릭
3. PR 대상 설정:
   - **base repository**: `roundielab-edu/mlops-cloud-project-mlops_11`
   - **head repository**: `yourusername/mlops-cloud-project-mlops_11`
4. 제목 및 설명 작성
5. `Create pull request` 클릭

---

## ✅ 전체 요약 흐름

```
[조 GitHub 레포]
    ↓ (Fork)
[개인 GitHub 레포: mlops-cloud-project-mlops_11]
    ↓ (Clone)
[개인 로컬 PC]
    ↓ (add → commit → push)
[개인 GitHub]
    ↓ (PR)
[조 GitHub 레포]
```

---

## 🛠 Git 명령 요약

| 명령 | 설명 |
|------|------|
| `git clone URL` | 레포를 로컬에 복제 |
| `git add <file>` | 변경 파일 스테이징 |
| `git commit -m "메시지"` | 변경 사항 커밋 |
| `git push origin main` | 원격 레포에 푸시 |
| `git pull origin main` | 원격 코드 동기화 |
