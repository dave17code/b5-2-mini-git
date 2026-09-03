# 🧩 B5-2 Mini Git

Python 3.10+에서 동작하는 **CLI 기반 Mini Git 프로그램**입니다.

이번 프로젝트는 실제 Git의 핵심 개념인 **Commit, Branch, DAG 구조**를 단순화해 구현하고,
그 위에 **DFS, BFS, Hash Map, Inverted Index, Merge Sort**를 직접 적용하는 것을 목표로 합니다.

> 🎯 **보너스 과제는 구현하지 않았으며, 미션의 필수 요구사항만 구현했습니다.**

---

# 🚀 실행 방법

프로젝트 루트에서 실행합니다.

```bash
python main.py
```

환경에 따라 아래 명령을 사용할 수도 있습니다.

```bash
python3 main.py
```

프로그램이 실행되면 다음과 같은 프롬프트가 나타납니다.

```text
mini-git>
```

종료 명령:

```text
exit
quit
```

---

# ⌨️ 지원 명령어

```text
INIT <user_name>

BRANCH <branch_name>
SWITCH <branch_name>
COMMIT <message>

LOG
LOG --sort-by=date
LOG --sort-by=author

PATH <commit1> <commit2>
ANCESTORS <commit_hash>

SEARCH <keyword>
SEARCH --author=<name>
```

---

# 📌 CLI 입력 규칙

명령어는 **대소문자를 구분하지 않습니다.**

예를 들어 아래 명령은 모두 동일하게 처리됩니다.

```text
INIT Alice
init Alice
Init Alice
```

사용자명, Commit 메시지, 검색어에 **공백이 포함될 경우 따옴표로 감쌉니다.**

```text
INIT "Alice Kim"
COMMIT "Add login feature"
SEARCH "login feature"
SEARCH --author="Alice Kim"
```

---

# 🏗️ 핵심 설계

## 1️⃣ Commit DAG

각 Commit은 최소한 다음 정보를 가집니다.

```text
hash
message
author
timestamp
parents
```

각 Commit은 부모 Commit의 hash를 `parents`에 저장합니다.

예:

```text
A ← B ← C
```

구조상:

```text
B.parents = [A]
C.parents = [B]
```

와 같은 형태입니다.

Commit 전체는 **DAG(Directed Acyclic Graph, 방향성 비순환 그래프)** 구조를 형성합니다.

Commit 저장소는 다음 형태의 Hash Map으로 관리합니다.

```text
commit_hash -> Commit 객체
```

Python에서는 `dict`를 사용하므로 Commit hash 기반 조회는 평균적으로:

```text
O(1)
```

입니다.

---

# 🌿 2️⃣ Branch / HEAD

Branch는 특정 Commit을 가리키는 참조입니다.

내부적으로:

```text
branch_name -> commit_hash
```

형태의 `dict`로 관리합니다.

예:

```text
main    -> c000003
feature -> c000002
```

현재 작업 중인 브랜치는:

```text
current_branch
```

가 나타냅니다.

새 Commit이 생성되면 현재 Branch가 새 Commit을 가리키도록 이동합니다.

```text
A ← B
    ↑
   main
```

새 Commit `C` 생성:

```text
A ← B ← C
        ↑
       main
```

---

# 🧭 3️⃣ LOG — DFS / 위상 정렬 성격

기본 `LOG`는 실제 Git처럼 단순 최신순으로 출력하지 않습니다.

미션 요구사항에 따라:

> **부모 Commit이 항상 자식 Commit보다 먼저 출력되도록 구현합니다.**

예:

```text
A ← B ← C
```

출력:

```text
A
B
C
```

이를 위해 **DFS(Depth First Search)** 를 사용합니다.

핵심 동작:

```text
현재 Commit 방문
        ↓
부모 Commit 먼저 탐색
        ↓
현재 Commit 출력
```

따라서 기본 `LOG`는 **위상 정렬 성격을 가진 출력 순서**를 만듭니다.

시간복잡도:

```text
O(V + E)
```

* `V` = Commit 수
* `E` = Commit 간 연결 수

---

# 🔎 4️⃣ PATH — BFS 최단 경로

```text
PATH <commit1> <commit2>
```

두 Commit 사이의 최단 경로를 찾습니다.

미션 요구사항에 따라 Commit과 Parent의 연결은 PATH 탐색 시:

```text
자식 → 부모
```

방향만 보는 것이 아니라:

```text
부모 ↔ 자식
```

의 **무방향 간선**으로 취급합니다.

예:

```text
A ← B ← C
     \
      ← D
```

PATH에서는:

```text
A ↔ B ↔ C
    ↕
    D
```

로 탐색합니다.

모든 간선의 비용이 동일하기 때문에 **BFS(Breadth First Search)** 를 사용하여 최단 경로를 찾습니다.

경로가 없으면:

```text
No path
```

를 출력합니다.

---

## 🔹 동일 길이 최단 경로 처리

최단 경로가 여러 개 존재할 경우:

```text
hash1->hash2->hash3
```

형태의 전체 경로 문자열을 기준으로 **사전순으로 가장 작은 경로**를 선택합니다.

이를 위해 BFS에서 탐색할 인접 Commit들을 **직접 구현한 Merge Sort**로 정렬합니다.

---

# 🧬 5️⃣ ANCESTORS — DFS

```text
ANCESTORS <commit_hash>
```

특정 Commit에서 부모 방향으로 도달 가능한 **모든 조상 Commit**을 탐색합니다.

예:

```text
A ← B ← C
```

```text
ANCESTORS C
```

결과:

```text
B
A
```

탐색에는 DFS를 사용합니다.

그래프에서 동일한 Commit을 여러 번 방문하는 것을 막기 위해:

```text
visited
```

집합을 사용합니다.

시간복잡도:

```text
O(V + E)
```

범위 내에서 동작합니다.

---

# 🔍 6️⃣ Inverted Index

검색 성능을 위해 Commit 생성 시 **역색인(Inverted Index)** 을 함께 갱신합니다.

두 종류의 인덱스를 지원합니다.

```text
keyword -> commit_hash 목록

author -> commit_hash 목록
```

---

## 🔹 Keyword Index

예를 들어 다음 Commit이 생성되었다고 가정합니다.

```text
COMMIT "Add login feature"
```

메시지를:

```text
split() + lower()
```

방식으로 정규화합니다.

결과:

```text
add
login
feature
```

그리고 다음처럼 저장합니다.

```text
add     -> [c000002]
login   -> [c000002]
feature -> [c000002]
```

따라서:

```text
SEARCH login
```

을 실행할 때 모든 Commit을 순회하지 않고:

```text
keyword_index["login"]
```

의 후보를 바로 가져옵니다.

---

## 🔹 Author Index

Author 역시 역색인으로 관리합니다.

```text
alice kim -> [c000001, c000002, c000003]
bob       -> [c000004]
```

따라서:

```text
SEARCH --author="Alice Kim"
```

을 실행하면 모든 Commit을 검색하지 않고 해당 Author의 posting 목록만 사용합니다.

---

## 🔹 공백이 포함된 Keyword 검색

예:

```text
SEARCH "add login"
```

검색어를:

```text
add
login
```

으로 분리한 뒤 각 Keyword posting list의 **교집합**을 구합니다.

즉 전체 Commit을 다시 순회하지 않고 역색인을 계속 활용합니다.

---

# 🔃 7️⃣ 직접 구현 Merge Sort

이번 미션에서는 Python의 표준 정렬 API 사용이 금지되어 있습니다.

따라서 아래 기능을 사용하지 않습니다.

```python
sorted()
list.sort()
```

대신 **Merge Sort를 직접 구현**하여 사용합니다.

지원하는 정렬 기준:

```text
LOG --sort-by=date
```

→ `timestamp` 기준 오름차순

```text
LOG --sort-by=author
```

→ `author` 이름 기준 오름차순

---

## 📊 Merge Sort 특성

| 구분    | 시간복잡도        |
| ----- | ------------ |
| 최선    | `O(N log N)` |
| 평균    | `O(N log N)` |
| 최악    | `O(N log N)` |
| 안정 정렬 | ✅ Yes        |

Merge Sort는 동일한 정렬 기준 값을 가진 요소들의 기존 상대 순서를 유지할 수 있는 **Stable Sort**입니다.

---

# 🧠 주요 자료구조 / 알고리즘

| 기능              | 핵심 자료구조 / 알고리즘    |
| --------------- | ----------------- |
| Commit 저장       | Hash Map (`dict`) |
| Commit Graph    | DAG               |
| Branch 관리       | Hash Map (`dict`) |
| 기본 `LOG`        | DFS / 위상 정렬 성격    |
| `ANCESTORS`     | DFS               |
| `PATH`          | BFS               |
| `SEARCH`        | Inverted Index    |
| `LOG --sort-by` | 직접 구현 Merge Sort  |
| 중복 방문 방지        | `set`             |
| BFS 탐색          | Queue             |

---

# ⏱️ 주요 시간복잡도

| 기능               | 핵심 구조 / 알고리즘   | 시간복잡도 개념                      |
| ---------------- | -------------- | ----------------------------- |
| Commit hash 조회   | Hash Map       | 평균 `O(1)`                     |
| 기본 `LOG`         | DFS            | `O(V + E)`                    |
| `ANCESTORS`      | DFS            | `O(V + E)` 범위 내               |
| `PATH`           | BFS            | `O(V + E)` + 인접 목록 정렬 비용      |
| `SEARCH keyword` | Inverted Index | 전체 Commit 순회 없이 posting 후보 중심 |
| `SEARCH author`  | Inverted Index | Author posting 후보 중심          |
| 정렬 `LOG`         | Merge Sort     | `O(N log N)`                  |

---

# ⚠️ 에러 처리

잘못된 입력이나 존재하지 않는 Branch / Commit에 대해 최소 에러 메시지를 제공합니다.

예:

```text
Invalid args
```

```text
Unknown branch: feature
```

```text
Unknown commit: c999999
```

```text
Repository not initialized.
```

---

# 💾 데이터 저장 범위

이번 프로젝트는 미션 제약사항에 따라 **메모리 기반으로만 동작합니다.**

따라서 다음 기능은 구현하지 않습니다.

```text
❌ 파일 내용 추적
❌ Staging Area
❌ 네트워크 통신
❌ Push / Pull
❌ 데이터 영속 저장
❌ 실제 .git 디렉터리 생성
```

프로그램이 종료되면 메모리에 있던 Repository 상태도 함께 사라집니다.

---

# 🎯 프로젝트 핵심 학습 포인트

이번 Mini Git 프로젝트에서 중요한 것은 실제 Git 전체를 복제하는 것이 아니라,
Git의 Commit 구조를 활용하여 다음 자료구조와 알고리즘을 직접 구현하는 것입니다.

```text
Commit
   ↓
Graph Node

parents
   ↓
Graph Edge

Commit Graph
   ↓
DAG

LOG
   ↓
DFS / Topological Ordering

PATH
   ↓
BFS Shortest Path

ANCESTORS
   ↓
DFS

SEARCH
   ↓
Inverted Index

Commit Lookup
   ↓
Hash Map

LOG --sort-by
   ↓
Merge Sort
```

즉, 이 프로젝트의 핵심은:

> **Git의 Commit DAG를 기반으로 그래프 탐색, 해시 기반 조회, 역색인 검색, 직접 구현 정렬 알고리즘을 하나의 CLI 프로그램 안에서 연결해 보는 것**입니다.
