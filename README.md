# B5-2 Mini Git

Python 3.10+에서 동작하는 **CLI 기반 Mini Git**입니다. 보너스 과제는 구현하지 않았고, 미션의 필수 요구사항만 구현했습니다.

## 실행

```bash
python main.py
```

종료:

```text
exit
quit
```

## 지원 명령어

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

명령어는 대소문자를 구분하지 않습니다. 공백이 포함된 사용자명, 커밋 메시지, 검색어는 따옴표로 감쌉니다.

```text
INIT "Alice Kim"
COMMIT "Add login feature"
SEARCH "login feature"
SEARCH --author="Alice Kim"
```

## 핵심 설계

### 1. Commit DAG

각 Commit은 다음 필드를 가집니다.

- `hash`
- `message`
- `author`
- `timestamp`
- `parents`

Commit은 부모 Commit의 hash를 보관하며, 저장소 전체는 DAG 형태로 동작합니다. `commits`는 `hash -> Commit` 형태의 `dict`이므로 평균적으로 빠른 hash 조회가 가능합니다.

### 2. Branch / HEAD

`branches`는 `branch_name -> commit_hash` 형태의 `dict`입니다. 현재 브랜치는 `current_branch`가 나타냅니다.

새 Commit을 만들면 현재 브랜치가 새 Commit hash를 가리키도록 이동합니다.

### 3. LOG

기본 `LOG`는 단순 최신순이 아니라 **부모가 자식보다 먼저 출력되도록** DFS 기반의 위상 정렬 성격 순서를 만듭니다.

### 4. PATH

부모-자식 연결을 **무방향 간선**으로 보고 BFS로 최단 경로를 찾습니다. 같은 길이의 최단 경로가 여러 개이면 hash 사전순으로 더 작은 경로가 먼저 탐색되도록 인접 노드를 직접 구현한 Merge Sort로 정렬합니다.

### 5. ANCESTORS

주어진 Commit에서 부모 방향으로 DFS를 수행하여 도달 가능한 모든 조상을 출력합니다. `visited` 집합으로 중복 방문을 방지합니다.

### 6. Inverted Index

Commit 생성 시 두 종류의 역색인을 즉시 갱신합니다.

```text
keyword -> commit_hash 목록
author  -> commit_hash 목록
```

키워드는 요구사항대로 `split()` + `lower()` 기준으로 정규화합니다. 검색 시 전체 Commit을 순회하지 않고 인덱스의 후보 목록을 사용합니다.

공백이 있는 검색어는 토큰별 posting list의 교집합으로 처리합니다.

### 7. 직접 구현 정렬

Python의 `sorted()`와 `list.sort()`를 사용하지 않습니다. 안정 정렬인 **Merge Sort**를 직접 구현했습니다.

- `LOG --sort-by=date`: timestamp 오름차순
- `LOG --sort-by=author`: author 이름 오름차순

Merge Sort 시간복잡도:

- 최선: `O(N log N)`
- 평균: `O(N log N)`
- 최악: `O(N log N)`
- 안정 정렬: Yes

## 주요 시간복잡도

| 기능 | 핵심 구조/알고리즘 | 시간복잡도 개념 |
|---|---|---|
| Commit hash 조회 | Hash Map | 평균 `O(1)` |
| 기본 LOG | DFS | `O(V + E)` |
| ANCESTORS | DFS | `O(V + E)` 범위 내 |
| PATH | BFS | `O(V + E)` + 인접 목록 정렬 비용 |
| SEARCH keyword | Inverted Index | 전체 순회 `O(N)` 대신 posting 후보 중심 |
| SEARCH author | Inverted Index | author posting 후보 중심 |
| 정렬 LOG | Merge Sort | `O(N log N)` |

## 에러 처리 예시

```text
Invalid args
Unknown branch: feature
Unknown commit: c999999
Repository not initialized.
```

## 데이터 저장 범위

미션 제약에 맞춰 파일 내용 추적, 네트워크, 영속 저장은 구현하지 않습니다. 프로그램 종료 시 메모리의 저장소 상태는 사라집니다.
