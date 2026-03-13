"""
Expanded training templates — 100+ real-world code patch, translation, and completion examples.

Covers:
- Systems languages (C, C++, Rust, Go, Zig)
- Scripting (Python, Ruby, Perl, Lua, Bash, PowerShell)
- Web (JavaScript, TypeScript, PHP, HTML/CSS)
- Mobile (Java, Kotlin, Swift, Dart)
- Embedded/Firmware (Arduino, ESP-IDF, MicroPython)
- Config/Build (YAML, JSON, TOML, Makefile, CMake, Dockerfile)
- Assembly (x86, ARM)
- Kernel/Driver patterns
- Parser/Compiler-compiler patterns (BNF, AST, lexer/parser)
- Package manager patterns (dependency resolution, manifests)
- ECL (Embeddable Common Lisp) patterns
- Loom/concurrency patterns
- Database/SQL patterns

Each tuple: (broken_code, fixed_code, gap_category, language)
"""

from typing import List, Tuple

# ============================================================================
# PATCH TEMPLATES — broken -> fixed code pairs
# ============================================================================

EXPANDED_PATCH_TEMPLATES: List[Tuple[str, str, str, str]] = [
    # -----------------------------------------------------------------------
    # C — Systems Programming
    # -----------------------------------------------------------------------
    (
        'char *buf = malloc(size);\nmemcpy(buf, src, size);',
        'char *buf = malloc(size);\nif (buf == NULL) return -1;\nmemcpy(buf, src, size);',
        "null_dereference", "c",
    ),
    (
        'char buf[64];\nstrcpy(buf, user_input);',
        'char buf[64];\nstrncpy(buf, user_input, sizeof(buf) - 1);\nbuf[sizeof(buf) - 1] = \'\\0\';',
        "buffer_overflow", "c",
    ),
    (
        'int *data = malloc(n * sizeof(int));\nprocess(data);\nreturn 0;',
        'int *data = malloc(n * sizeof(int));\nif (data == NULL) return -ENOMEM;\nprocess(data);\nfree(data);\nreturn 0;',
        "resource_leak", "c",
    ),
    (
        'int result;\nif (x > 0) result = x * 2;\nreturn result;',
        'int result = 0;\nif (x > 0) result = x * 2;\nreturn result;',
        "uninitialized_variable", "c",
    ),
    (
        'int get_element(int *arr, int idx) {\n    return arr[idx];\n}',
        'int get_element(int *arr, int idx, int len) {\n    if (idx < 0 || idx >= len) return -1;\n    return arr[idx];\n}',
        "missing_bounds_check", "c",
    ),
    (
        'void process(char *input) {\n    char buf[256];\n    sprintf(buf, "Data: %s", input);\n}',
        'void process(char *input) {\n    char buf[256];\n    snprintf(buf, sizeof(buf), "Data: %s", input);\n}',
        "buffer_overflow", "c",
    ),
    (
        'FILE *fp = fopen(path, "r");\nchar line[1024];\nfgets(line, sizeof(line), fp);\nfclose(fp);',
        'FILE *fp = fopen(path, "r");\nif (fp == NULL) {\n    perror("fopen");\n    return -1;\n}\nchar line[1024];\nif (fgets(line, sizeof(line), fp) == NULL) {\n    fclose(fp);\n    return -1;\n}\nfclose(fp);',
        "missing_error_handling", "c",
    ),
    (
        'int *p = malloc(sizeof(int));\n*p = 42;\nfree(p);\nprintf("%d\\n", *p);',
        'int *p = malloc(sizeof(int));\nif (p == NULL) return -1;\n*p = 42;\nint val = *p;\nfree(p);\np = NULL;\nprintf("%d\\n", val);',
        "resource_leak", "c",
    ),
    (
        'void handle_signal(int sig) {\n    printf("Signal %d\\n", sig);\n    exit(1);\n}',
        'volatile sig_atomic_t got_signal = 0;\nvoid handle_signal(int sig) {\n    got_signal = sig;\n}\n// In main loop: if (got_signal) { /* cleanup */ exit(1); }',
        "race_condition", "c",
    ),
    (
        'int sum = 0;\nfor (int i = 0; i <= n; i++) {\n    sum += arr[i];\n}',
        'int sum = 0;\nfor (int i = 0; i < n; i++) {\n    sum += arr[i];\n}',
        "missing_bounds_check", "c",
    ),
    (
        'int fd = open(path, O_RDONLY);\nread(fd, buf, sizeof(buf));\nclose(fd);',
        'int fd = open(path, O_RDONLY);\nif (fd < 0) {\n    perror("open");\n    return -1;\n}\nssize_t n = read(fd, buf, sizeof(buf));\nif (n < 0) {\n    perror("read");\n    close(fd);\n    return -1;\n}\nclose(fd);',
        "missing_error_handling", "c",
    ),
    (
        'pthread_mutex_t lock;\nvoid increment() {\n    counter++;\n}',
        'pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;\nvoid increment() {\n    pthread_mutex_lock(&lock);\n    counter++;\n    pthread_mutex_unlock(&lock);\n}',
        "race_condition", "c",
    ),
    (
        'uint8_t a = 200;\nuint8_t b = 100;\nuint8_t sum = a + b;',
        'uint8_t a = 200;\nuint8_t b = 100;\nuint16_t sum = (uint16_t)a + (uint16_t)b;\nif (sum > UINT8_MAX) { /* overflow */ }',
        "security_vulnerability", "c",
    ),

    # -----------------------------------------------------------------------
    # C++ — Modern C++
    # -----------------------------------------------------------------------
    (
        'int getValue(std::vector<int>& v, int i) {\n    return v[i];\n}',
        'int getValue(const std::vector<int>& v, size_t i) {\n    return v.at(i);\n}',
        "missing_bounds_check", "cpp",
    ),
    (
        'Base* obj = new Derived();\ndelete obj;',
        'std::unique_ptr<Base> obj = std::make_unique<Derived>();',
        "resource_leak", "cpp",
    ),
    (
        'std::string& getName() {\n    std::string name = "test";\n    return name;\n}',
        'std::string getName() {\n    return "test";\n}',
        "resource_leak", "cpp",
    ),
    (
        'char* data = new char[size];\nprocess(data);\n// forgot delete',
        'auto data = std::make_unique<char[]>(size);\nprocess(data.get());',
        "resource_leak", "cpp",
    ),
    (
        'template<typename T>\nT divide(T a, T b) {\n    return a / b;\n}',
        'template<typename T>\nT divide(T a, T b) {\n    if (b == T{}) throw std::domain_error("division by zero");\n    return a / b;\n}',
        "missing_error_handling", "cpp",
    ),
    (
        'class Mutex {\npublic:\n    void lock() { mtx.lock(); }\n    void process() { /* may throw */ }\n    void unlock() { mtx.unlock(); }\n};',
        'class Mutex {\npublic:\n    void process() {\n        std::lock_guard<std::mutex> guard(mtx);\n        /* may throw - lock_guard handles unlock */\n    }\n};',
        "race_condition", "cpp",
    ),
    (
        'std::thread t([]{ heavy_work(); });\n// forgot join',
        'std::thread t([]{ heavy_work(); });\nt.join();',
        "resource_leak", "cpp",
    ),
    (
        'auto it = map.find(key);\nreturn it->second;',
        'auto it = map.find(key);\nif (it == map.end()) {\n    throw std::out_of_range("key not found");\n}\nreturn it->second;',
        "null_dereference", "cpp",
    ),

    # -----------------------------------------------------------------------
    # Python
    # -----------------------------------------------------------------------
    (
        'def read_config(path):\n    f = open(path)\n    data = json.load(f)\n    return data',
        'def read_config(path):\n    try:\n        with open(path) as f:\n            data = json.load(f)\n        return data\n    except (FileNotFoundError, json.JSONDecodeError) as e:\n        logging.error(f"Config error: {e}")\n        return {}',
        "missing_error_handling", "python",
    ),
    (
        'def parse_date(s):\n    return datetime.strptime(s, "%Y-%m-%d")',
        'from datetime import datetime\n\ndef parse_date(s):\n    return datetime.strptime(s, "%Y-%m-%d")',
        "missing_import", "python",
    ),
    (
        'class DataProcessor:\n    def process(self, data):\n        pass  # TODO: implement',
        'class DataProcessor:\n    def process(self, data):\n        if not data:\n            return []\n        return [self._transform(item) for item in data]\n\n    def _transform(self, item):\n        return item.strip().lower()',
        "incomplete_implementation", "python",
    ),
    (
        'def calculate(x, y, op):\n    if op == "add":\n        return x + y\n    elif op == "sub":\n        return x - y',
        'def calculate(x, y, op):\n    if op == "add":\n        return x + y\n    elif op == "sub":\n        return x - y\n    else:\n        raise ValueError(f"Unknown op: {op}")',
        "missing_return", "python",
    ),
    (
        'query = f"SELECT * FROM users WHERE name = \'{username}\'"',
        'query = "SELECT * FROM users WHERE name = ?"\ncursor.execute(query, (username,))',
        "security_vulnerability", "python",
    ),
    (
        'def download(url):\n    resp = requests.get(url)\n    return resp.json()',
        'def download(url, timeout=30):\n    try:\n        resp = requests.get(url, timeout=timeout)\n        resp.raise_for_status()\n        return resp.json()\n    except requests.RequestException as e:\n        logging.error(f"Download failed: {e}")\n        return None',
        "missing_error_handling", "python",
    ),
    (
        'def divide(a, b):\n    return a / b',
        'def divide(a, b):\n    if b == 0:\n        raise ZeroDivisionError("Cannot divide by zero")\n    return a / b',
        "missing_error_handling", "python",
    ),
    (
        'data = pickle.loads(user_input)',
        'data = json.loads(user_input)  # Never unpickle untrusted data',
        "security_vulnerability", "python",
    ),
    (
        'def get_user(user_id):\n    conn = sqlite3.connect("db.sqlite")\n    cursor = conn.cursor()\n    cursor.execute(f"SELECT * FROM users WHERE id={user_id}")\n    return cursor.fetchone()',
        'def get_user(user_id):\n    with sqlite3.connect("db.sqlite") as conn:\n        cursor = conn.cursor()\n        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))\n        return cursor.fetchone()',
        "security_vulnerability", "python",
    ),
    (
        'threads = []\nfor i in range(10):\n    t = threading.Thread(target=worker, args=(shared_list,))\n    threads.append(t)\n    t.start()',
        'lock = threading.Lock()\nthreads = []\nfor i in range(10):\n    t = threading.Thread(target=worker, args=(shared_list, lock))\n    threads.append(t)\n    t.start()\nfor t in threads:\n    t.join()',
        "race_condition", "python",
    ),
    (
        'class Logger:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance',
        'import threading\n\nclass Logger:\n    _instance = None\n    _lock = threading.Lock()\n    def __new__(cls):\n        with cls._lock:\n            if cls._instance is None:\n                cls._instance = super().__new__(cls)\n        return cls._instance',
        "race_condition", "python",
    ),
    (
        'os.system(f"rm -rf {user_path}")',
        'import shlex\npath = shlex.quote(user_path)\nsubprocess.run(["rm", "-rf", path], check=True)',
        "security_vulnerability", "python",
    ),

    # -----------------------------------------------------------------------
    # Rust
    # -----------------------------------------------------------------------
    (
        'fn read_file(path: &str) -> String {\n    std::fs::read_to_string(path).unwrap()\n}',
        'fn read_file(path: &str) -> Result<String, std::io::Error> {\n    std::fs::read_to_string(path)\n}',
        "missing_error_handling", "rust",
    ),
    (
        'fn get_first(v: &Vec<i32>) -> i32 {\n    v[0]\n}',
        'fn get_first(v: &[i32]) -> Option<i32> {\n    v.first().copied()\n}',
        "missing_bounds_check", "rust",
    ),
    (
        'fn parse_int(s: &str) -> i32 {\n    s.parse().unwrap()\n}',
        'fn parse_int(s: &str) -> Result<i32, std::num::ParseIntError> {\n    s.parse()\n}',
        "missing_error_handling", "rust",
    ),
    (
        'unsafe {\n    let ptr: *mut i32 = std::ptr::null_mut();\n    *ptr = 42;\n}',
        'let mut val: i32 = 0;\nval = 42;',
        "null_dereference", "rust",
    ),
    (
        'fn longest(a: &str, b: &str) -> &str {\n    if a.len() > b.len() { a } else { b }\n}',
        "fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {\n    if a.len() > b.len() { a } else { b }\n}",
        "type_mismatch", "rust",
    ),
    (
        'use std::sync::Mutex;\nlet data = Mutex::new(vec![1, 2, 3]);\nlet val = data.lock().unwrap();\n// deadlock: locking again\nlet val2 = data.lock().unwrap();',
        'use std::sync::Mutex;\nlet data = Mutex::new(vec![1, 2, 3]);\n{\n    let val = data.lock().unwrap();\n    // use val\n}\n// lock released, safe to lock again\nlet val2 = data.lock().unwrap();',
        "race_condition", "rust",
    ),

    # -----------------------------------------------------------------------
    # Go
    # -----------------------------------------------------------------------
    (
        'func readFile(path string) []byte {\n    data, _ := os.ReadFile(path)\n    return data\n}',
        'func readFile(path string) ([]byte, error) {\n    data, err := os.ReadFile(path)\n    if err != nil {\n        return nil, fmt.Errorf("read %s: %w", path, err)\n    }\n    return data, nil\n}',
        "missing_error_handling", "go",
    ),
    (
        'func handler(w http.ResponseWriter, r *http.Request) {\n    body, _ := io.ReadAll(r.Body)\n    var data map[string]interface{}\n    json.Unmarshal(body, &data)\n    fmt.Fprintf(w, "Got: %v", data)\n}',
        'func handler(w http.ResponseWriter, r *http.Request) {\n    body, err := io.ReadAll(r.Body)\n    if err != nil {\n        http.Error(w, "Bad request", http.StatusBadRequest)\n        return\n    }\n    defer r.Body.Close()\n    var data map[string]interface{}\n    if err := json.Unmarshal(body, &data); err != nil {\n        http.Error(w, "Invalid JSON", http.StatusBadRequest)\n        return\n    }\n    fmt.Fprintf(w, "Got: %v", data)\n}',
        "missing_error_handling", "go",
    ),
    (
        'var counter int\nfunc increment() {\n    counter++\n}',
        'var (\n    counter int\n    mu      sync.Mutex\n)\nfunc increment() {\n    mu.Lock()\n    defer mu.Unlock()\n    counter++\n}',
        "race_condition", "go",
    ),
    (
        'func processItems(items []string) {\n    for i := 0; i <= len(items); i++ {\n        fmt.Println(items[i])\n    }\n}',
        'func processItems(items []string) {\n    for i := 0; i < len(items); i++ {\n        fmt.Println(items[i])\n    }\n}',
        "missing_bounds_check", "go",
    ),
    (
        'ch := make(chan int)\ngo func() { ch <- 42 }()\ngo func() { ch <- 43 }()\nfmt.Println(<-ch)',
        'ch := make(chan int, 2)\nvar wg sync.WaitGroup\nwg.Add(2)\ngo func() { defer wg.Done(); ch <- 42 }()\ngo func() { defer wg.Done(); ch <- 43 }()\ngo func() { wg.Wait(); close(ch) }()\nfor v := range ch { fmt.Println(v) }',
        "race_condition", "go",
    ),

    # -----------------------------------------------------------------------
    # JavaScript / TypeScript
    # -----------------------------------------------------------------------
    (
        'async function fetchData(url) {\n    const res = await fetch(url);\n    return res.json();\n}',
        'async function fetchData(url) {\n    try {\n        const res = await fetch(url);\n        if (!res.ok) throw new Error(`HTTP ${res.status}`);\n        return await res.json();\n    } catch (err) {\n        console.error("Fetch failed:", err);\n        return null;\n    }\n}',
        "missing_error_handling", "javascript",
    ),
    (
        'function add(a, b) {\n    return a + b;\n}',
        'function add(a: number, b: number): number {\n    return a + b;\n}',
        "type_mismatch", "typescript",
    ),
    (
        'document.innerHTML = userInput;',
        'document.textContent = userInput;  // Prevent XSS',
        "security_vulnerability", "javascript",
    ),
    (
        'const data = JSON.parse(input);\nreturn data.user.name;',
        'try {\n    const data = JSON.parse(input);\n    return data?.user?.name ?? "unknown";\n} catch {\n    return "unknown";\n}',
        "missing_error_handling", "javascript",
    ),
    (
        'app.get("/user/:id", (req, res) => {\n    const user = db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);\n    res.json(user);\n});',
        'app.get("/user/:id", (req, res) => {\n    const id = parseInt(req.params.id, 10);\n    if (isNaN(id)) return res.status(400).json({ error: "Invalid ID" });\n    const user = db.query("SELECT * FROM users WHERE id = ?", [id]);\n    res.json(user);\n});',
        "security_vulnerability", "javascript",
    ),
    (
        'const items = getItems();\nitems.forEach(async (item) => {\n    await processItem(item);\n});',
        'const items = getItems();\nfor (const item of items) {\n    await processItem(item);\n}',
        "race_condition", "javascript",
    ),
    (
        'function readFile(path: string): string {\n    return fs.readFileSync(path).toString();\n}',
        'function readFile(path: string): string {\n    if (!fs.existsSync(path)) {\n        throw new Error(`File not found: ${path}`);\n    }\n    return fs.readFileSync(path, "utf-8");\n}',
        "missing_error_handling", "typescript",
    ),
    (
        'const result: any = getData();\nconsole.log(result.name);',
        'interface DataResult {\n    name: string;\n    id: number;\n}\nconst result: DataResult = getData();\nconsole.log(result.name);',
        "type_mismatch", "typescript",
    ),

    # -----------------------------------------------------------------------
    # Java
    # -----------------------------------------------------------------------
    (
        'FileInputStream fis = new FileInputStream(file);\nbyte[] data = fis.readAllBytes();\nreturn data;',
        'try (FileInputStream fis = new FileInputStream(file)) {\n    return fis.readAllBytes();\n}',
        "resource_leak", "java",
    ),
    (
        'String name = request.getParameter("name");\nStatement stmt = conn.createStatement();\nstmt.executeQuery("SELECT * FROM users WHERE name=\'" + name + "\'");',
        'String name = request.getParameter("name");\nPreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE name=?");\nstmt.setString(1, name);\nstmt.executeQuery();',
        "security_vulnerability", "java",
    ),
    (
        'public String toString() {\n    return name + " " + age;\n}',
        '@Override\npublic String toString() {\n    return String.format("%s %d", name, age);\n}',
        "incomplete_implementation", "java",
    ),
    (
        'List<String> items = new ArrayList<>();\nfor (String item : items) {\n    if (item.equals("remove")) {\n        items.remove(item);\n    }\n}',
        'List<String> items = new ArrayList<>();\nitems.removeIf(item -> item.equals("remove"));',
        "race_condition", "java",
    ),
    (
        'Object obj = map.get(key);\nString value = (String) obj;',
        'Object obj = map.get(key);\nif (obj == null) throw new NoSuchElementException("Key not found: " + key);\nif (!(obj instanceof String)) throw new ClassCastException("Expected String");\nString value = (String) obj;',
        "null_dereference", "java",
    ),

    # -----------------------------------------------------------------------
    # Bash
    # -----------------------------------------------------------------------
    (
        '#!/bin/bash\ncd $1\nrm -rf build/\nmake',
        '#!/bin/bash\nset -euo pipefail\ncd "$1" || exit 1\nrm -rf build/\nmake',
        "missing_error_handling", "bash",
    ),
    (
        'for f in $(ls *.txt); do\n    cat $f\ndone',
        'for f in *.txt; do\n    [ -f "$f" ] || continue\n    cat "$f"\ndone',
        "missing_error_handling", "bash",
    ),
    (
        'eval "$USER_INPUT"',
        '# Never eval user input!\necho "Invalid operation" >&2\nexit 1',
        "security_vulnerability", "bash",
    ),
    (
        'TEMP=/tmp/data.txt\necho "$SECRET" > $TEMP\nprocess $TEMP',
        'TEMP=$(mktemp)\ntrap "rm -f $TEMP" EXIT\necho "$SECRET" > "$TEMP"\nchmod 600 "$TEMP"\nprocess "$TEMP"',
        "security_vulnerability", "bash",
    ),
    (
        'if [ $count -gt 10 ]; then\n    echo "too many"\nfi',
        'if [ "${count:-0}" -gt 10 ]; then\n    echo "too many"\nfi',
        "uninitialized_variable", "bash",
    ),

    # -----------------------------------------------------------------------
    # Arduino / ESP32 / Embedded
    # -----------------------------------------------------------------------
    (
        'void setup() {\n    WiFi.begin(ssid, password);\n    Serial.println(WiFi.localIP());\n}',
        'void setup() {\n    WiFi.begin(ssid, password);\n    int retries = 0;\n    while (WiFi.status() != WL_CONNECTED && retries < 20) {\n        delay(500);\n        retries++;\n    }\n    if (WiFi.status() == WL_CONNECTED) {\n        Serial.println(WiFi.localIP());\n    } else {\n        Serial.println("WiFi connection failed");\n    }\n}',
        "missing_error_handling", "arduino_cpp",
    ),
    (
        'void loop() {\n    int val = analogRead(A0);\n    char buf[8];\n    sprintf(buf, "%d", val);\n    Serial.println(buf);\n}',
        'void loop() {\n    int val = analogRead(A0);\n    char buf[16];\n    snprintf(buf, sizeof(buf), "%d", val);\n    Serial.println(buf);\n    delay(100);\n}',
        "buffer_overflow", "arduino_cpp",
    ),
    (
        'void setup() {\n    Serial.begin(115200);\n    EEPROM.begin(512);\n    String data = EEPROM.readString(0);\n}',
        'void setup() {\n    Serial.begin(115200);\n    if (!EEPROM.begin(512)) {\n        Serial.println("EEPROM init failed");\n        return;\n    }\n    String data = EEPROM.readString(0);\n    if (data.length() == 0) {\n        Serial.println("No saved data");\n    }\n}',
        "missing_error_handling", "arduino_cpp",
    ),
    (
        'void handleInterrupt() {\n    Serial.println("Interrupt!");\n    delay(100);\n}',
        'volatile bool interruptFlag = false;\nvoid IRAM_ATTR handleInterrupt() {\n    interruptFlag = true;\n}\n// In loop(): if (interruptFlag) { interruptFlag = false; Serial.println("Interrupt!"); }',
        "race_condition", "arduino_cpp",
    ),

    # -----------------------------------------------------------------------
    # Kotlin
    # -----------------------------------------------------------------------
    (
        'fun getUser(id: Int): User {\n    return users[id]\n}',
        'fun getUser(id: Int): User? {\n    return users.getOrNull(id)\n}',
        "missing_bounds_check", "kotlin",
    ),
    (
        'val name: String = intent.getStringExtra("name")',
        'val name: String = intent.getStringExtra("name") ?: "unknown"',
        "null_dereference", "kotlin",
    ),

    # -----------------------------------------------------------------------
    # Swift
    # -----------------------------------------------------------------------
    (
        'func loadData() -> String {\n    let data = try! String(contentsOfFile: path)\n    return data\n}',
        'func loadData() -> String? {\n    do {\n        return try String(contentsOfFile: path)\n    } catch {\n        print("Error loading: \\(error)")\n        return nil\n    }\n}',
        "missing_error_handling", "swift",
    ),
    (
        'let value = dict["key"]!\nprint(value)',
        'guard let value = dict["key"] else {\n    print("Key not found")\n    return\n}\nprint(value)',
        "null_dereference", "swift",
    ),

    # -----------------------------------------------------------------------
    # Ruby
    # -----------------------------------------------------------------------
    (
        'def read_file(path)\n  File.read(path)\nend',
        'def read_file(path)\n  File.read(path)\nrescue Errno::ENOENT => e\n  puts "File not found: #{e.message}"\n  nil\nend',
        "missing_error_handling", "ruby",
    ),
    (
        'system("rm -rf #{user_input}")',
        'require "shellwords"\nsystem("rm", "-rf", Shellwords.escape(user_input))',
        "security_vulnerability", "ruby",
    ),

    # -----------------------------------------------------------------------
    # PHP
    # -----------------------------------------------------------------------
    (
        '$query = "SELECT * FROM users WHERE id = " . $_GET["id"];\n$result = mysqli_query($conn, $query);',
        '$stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");\n$stmt->bind_param("i", $_GET["id"]);\n$stmt->execute();\n$result = $stmt->get_result();',
        "security_vulnerability", "php",
    ),
    (
        'echo $_GET["name"];',
        'echo htmlspecialchars($_GET["name"], ENT_QUOTES, "UTF-8");',
        "security_vulnerability", "php",
    ),

    # -----------------------------------------------------------------------
    # Lua
    # -----------------------------------------------------------------------
    (
        'function readConfig(path)\n    local f = io.open(path)\n    local data = f:read("*a")\n    f:close()\n    return data\nend',
        'function readConfig(path)\n    local f, err = io.open(path, "r")\n    if not f then\n        return nil, "Cannot open: " .. (err or "unknown")\n    end\n    local data = f:read("*a")\n    f:close()\n    return data\nend',
        "missing_error_handling", "lua",
    ),

    # -----------------------------------------------------------------------
    # Assembly (x86) — pattern recognition
    # -----------------------------------------------------------------------
    (
        'mov eax, [ebx]\ncall process\n; no stack frame setup',
        'push ebp\nmov ebp, esp\nsub esp, 16\nmov eax, [ebx]\ncall process\nmov esp, ebp\npop ebp\nret',
        "missing_error_handling", "assembly",
    ),
    (
        'mov eax, [esi]\nadd esi, 4\ncmp esi, edi\njle loop_start',
        'mov eax, [esi]\nadd esi, 4\ncmp esi, edi\njl loop_start  ; use jl not jle to avoid off-by-one',
        "missing_bounds_check", "assembly",
    ),

    # -----------------------------------------------------------------------
    # SQL
    # -----------------------------------------------------------------------
    (
        'DELETE FROM orders;',
        'DELETE FROM orders WHERE status = "cancelled" AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);',
        "missing_bounds_check", "sql",
    ),
    (
        'SELECT * FROM users;',
        'SELECT id, name, email FROM users LIMIT 100;',
        "incomplete_implementation", "sql",
    ),

    # -----------------------------------------------------------------------
    # Dockerfile
    # -----------------------------------------------------------------------
    (
        'FROM python:latest\nCOPY . /app\nRUN pip install -r requirements.txt\nCMD ["python", "app.py"]',
        'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nUSER 1000\nCMD ["python", "app.py"]',
        "security_vulnerability", "dockerfile",
    ),

    # -----------------------------------------------------------------------
    # YAML / Config
    # -----------------------------------------------------------------------
    (
        'apiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - name: app\n    image: myapp\n    ports:\n    - containerPort: 8080',
        'apiVersion: v1\nkind: Pod\nmetadata:\n  name: myapp\nspec:\n  containers:\n  - name: app\n    image: myapp:1.0.0\n    ports:\n    - containerPort: 8080\n    resources:\n      limits:\n        memory: "256Mi"\n        cpu: "500m"\n    livenessProbe:\n      httpGet:\n        path: /health\n        port: 8080',
        "incomplete_implementation", "yaml",
    ),

    # -----------------------------------------------------------------------
    # Makefile
    # -----------------------------------------------------------------------
    (
        'build:\n\tgcc -o app main.c\n\nclean:\n\trm app',
        'CC ?= gcc\nCFLAGS ?= -Wall -Wextra -O2\n\n.PHONY: build clean\n\nbuild: app\n\napp: main.c\n\t$(CC) $(CFLAGS) -o $@ $<\n\nclean:\n\trm -f app',
        "incomplete_implementation", "makefile",
    ),

    # -----------------------------------------------------------------------
    # CMake
    # -----------------------------------------------------------------------
    (
        'add_executable(app main.cpp)\ntarget_link_libraries(app pthread)',
        'cmake_minimum_required(VERSION 3.14)\nproject(app LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\nset(CMAKE_CXX_STANDARD_REQUIRED ON)\n\nadd_executable(app main.cpp)\ntarget_link_libraries(app PRIVATE Threads::Threads)\nfind_package(Threads REQUIRED)',
        "incomplete_implementation", "cmake",
    ),

    # -----------------------------------------------------------------------
    # Perl
    # -----------------------------------------------------------------------
    (
        'open(FILE, $filename);\nwhile (<FILE>) { print; }\nclose(FILE);',
        'open(my $fh, "<", $filename) or die "Cannot open $filename: $!";\nwhile (my $line = <$fh>) { print $line; }\nclose($fh);',
        "missing_error_handling", "perl",
    ),

    # -----------------------------------------------------------------------
    # ECL (Embeddable Common Lisp) patterns
    # -----------------------------------------------------------------------
    (
        '(defun read-data (path)\n  (with-open-file (s path)\n    (read s)))',
        '(defun read-data (path)\n  (handler-case\n    (with-open-file (s path :direction :input :if-does-not-exist nil)\n      (when s (read s nil nil)))\n    (error (c) (format t "Error reading ~a: ~a~%" path c) nil)))',
        "missing_error_handling", "lisp",
    ),
    (
        '(defun divide (a b)\n  (/ a b))',
        '(defun divide (a b)\n  (if (zerop b)\n    (error "Division by zero")\n    (/ a b)))',
        "missing_error_handling", "lisp",
    ),
    (
        '(defun process-list (lst)\n  (mapcar #\'car lst))',
        '(defun process-list (lst)\n  (mapcar (lambda (x)\n    (if (consp x) (car x) x)) lst))',
        "null_dereference", "lisp",
    ),

    # -----------------------------------------------------------------------
    # Zig
    # -----------------------------------------------------------------------
    (
        'fn readFile(path: []const u8) ![]u8 {\n    const file = try std.fs.cwd().openFile(path, .{});\n    return try file.readToEndAlloc(allocator, 1024 * 1024);\n}',
        'fn readFile(path: []const u8) ![]u8 {\n    const file = try std.fs.cwd().openFile(path, .{});\n    defer file.close();\n    return try file.readToEndAlloc(allocator, 1024 * 1024);\n}',
        "resource_leak", "zig",
    ),

    # -----------------------------------------------------------------------
    # Haskell
    # -----------------------------------------------------------------------
    (
        'readConfig :: FilePath -> IO String\nreadConfig path = readFile path',
        'readConfig :: FilePath -> IO (Either String String)\nreadConfig path = do\n  exists <- doesFileExist path\n  if exists\n    then Right <$> readFile path\n    else return $ Left $ "File not found: " ++ path',
        "missing_error_handling", "haskell",
    ),

    # -----------------------------------------------------------------------
    # Dart (Flutter)
    # -----------------------------------------------------------------------
    (
        'Future<String> fetchData() async {\n  final response = await http.get(Uri.parse(url));\n  return response.body;\n}',
        'Future<String?> fetchData() async {\n  try {\n    final response = await http.get(Uri.parse(url));\n    if (response.statusCode == 200) {\n      return response.body;\n    }\n    return null;\n  } catch (e) {\n    debugPrint("Fetch error: $e");\n    return null;\n  }\n}',
        "missing_error_handling", "dart",
    ),

    # -----------------------------------------------------------------------
    # Terraform
    # -----------------------------------------------------------------------
    (
        'resource "aws_s3_bucket" "data" {\n  bucket = "my-data-bucket"\n}',
        'resource "aws_s3_bucket" "data" {\n  bucket = "my-data-bucket"\n}\n\nresource "aws_s3_bucket_versioning" "data" {\n  bucket = aws_s3_bucket.data.id\n  versioning_configuration {\n    status = "Enabled"\n  }\n}\n\nresource "aws_s3_bucket_server_side_encryption_configuration" "data" {\n  bucket = aws_s3_bucket.data.id\n  rule {\n    apply_server_side_encryption_by_default {\n      sse_algorithm = "AES256"\n    }\n  }\n}',
        "security_vulnerability", "terraform",
    ),

    # -----------------------------------------------------------------------
    # GraphQL
    # -----------------------------------------------------------------------
    (
        'type Query {\n  user(id: ID!): User\n}\n\ntype User {\n  name: String\n  email: String\n}',
        'type Query {\n  user(id: ID!): User\n}\n\ntype User {\n  id: ID!\n  name: String!\n  email: String!\n  createdAt: DateTime!\n}\n\nscalar DateTime',
        "type_mismatch", "graphql",
    ),

    # -----------------------------------------------------------------------
    # Protobuf
    # -----------------------------------------------------------------------
    (
        'message User {\n  string name = 1;\n  int32 age = 2;\n}',
        'syntax = "proto3";\n\npackage myapp;\n\nmessage User {\n  string name = 1;\n  int32 age = 2;\n  string email = 3;\n  google.protobuf.Timestamp created_at = 4;\n}\n\nimport "google/protobuf/timestamp.proto";',
        "incomplete_implementation", "protobuf",
    ),

    # -----------------------------------------------------------------------
    # Kernel / Driver patterns
    # -----------------------------------------------------------------------
    (
        'static int __init mydriver_init(void) {\n    printk(KERN_INFO "Driver loaded\\n");\n    return 0;\n}',
        'static int __init mydriver_init(void) {\n    int ret;\n    ret = register_chrdev(MAJOR_NUM, DEVICE_NAME, &fops);\n    if (ret < 0) {\n        printk(KERN_ALERT "Failed to register: %d\\n", ret);\n        return ret;\n    }\n    printk(KERN_INFO "Driver loaded, major=%d\\n", MAJOR_NUM);\n    return 0;\n}\n\nstatic void __exit mydriver_exit(void) {\n    unregister_chrdev(MAJOR_NUM, DEVICE_NAME);\n    printk(KERN_INFO "Driver unloaded\\n");\n}\n\nmodule_init(mydriver_init);\nmodule_exit(mydriver_exit);\nMODULE_LICENSE("GPL");',
        "incomplete_implementation", "c",
    ),

    # -----------------------------------------------------------------------
    # Parser / Compiler-compiler patterns
    # -----------------------------------------------------------------------
    (
        'def parse_expr(tokens):\n    left = parse_term(tokens)\n    if tokens.peek() == "+":\n        tokens.advance()\n        right = parse_expr(tokens)\n        return ("add", left, right)\n    return left',
        'def parse_expr(tokens):\n    left = parse_term(tokens)\n    while tokens.peek() in ("+", "-"):\n        op = tokens.advance()\n        right = parse_term(tokens)\n        left = (op, left, right)\n    return left',
        "incomplete_implementation", "python",
    ),
    (
        'class Lexer:\n    def tokenize(self, source):\n        tokens = []\n        i = 0\n        while i < len(source):\n            if source[i].isdigit():\n                tokens.append(("NUM", source[i]))\n                i += 1',
        'class Lexer:\n    def tokenize(self, source):\n        tokens = []\n        i = 0\n        while i < len(source):\n            if source[i].isspace():\n                i += 1\n                continue\n            if source[i].isdigit():\n                num = ""\n                while i < len(source) and source[i].isdigit():\n                    num += source[i]\n                    i += 1\n                tokens.append(("NUM", int(num)))\n            elif source[i] in "+-*/()":\n                tokens.append(("OP", source[i]))\n                i += 1\n            else:\n                raise SyntaxError(f"Unexpected char: {source[i]}")\n        tokens.append(("EOF", None))\n        return tokens',
        "incomplete_implementation", "python",
    ),

    # -----------------------------------------------------------------------
    # Package manager / dependency patterns
    # -----------------------------------------------------------------------
    (
        '{\n  "dependencies": {\n    "express": "*",\n    "lodash": "*"\n  }\n}',
        '{\n  "dependencies": {\n    "express": "^4.18.0",\n    "lodash": "^4.17.21"\n  },\n  "engines": {\n    "node": ">=18.0.0"\n  }\n}',
        "security_vulnerability", "json",
    ),
]


# ============================================================================
# EXPANDED TRANSLATION TEMPLATES
# ============================================================================

EXPANDED_TRANSLATION_TEMPLATES: List[Tuple[str, str, str, str]] = [
    # Python -> C
    (
        'def add(a, b):\n    return a + b',
        'int add(int a, int b) {\n    return a + b;\n}',
        "python", "c",
    ),
    # Python -> Rust
    (
        'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)',
        'fn factorial(n: u64) -> u64 {\n    if n <= 1 {\n        return 1;\n    }\n    n * factorial(n - 1)\n}',
        "python", "rust",
    ),
    # Python -> JavaScript
    (
        'def greet(name):\n    return f"Hello, {name}!"',
        'function greet(name) {\n    return `Hello, ${name}!`;\n}',
        "python", "javascript",
    ),
    # C -> Python
    (
        'int max(int a, int b) {\n    return a > b ? a : b;\n}',
        'def max_val(a, b):\n    return a if a > b else b',
        "c", "python",
    ),
    # JavaScript -> Python
    (
        'const arr = [1, 2, 3];\nconst doubled = arr.map(x => x * 2);',
        'arr = [1, 2, 3]\ndoubled = [x * 2 for x in arr]',
        "javascript", "python",
    ),
    # Bash -> Python
    (
        'for f in *.txt; do\n    wc -l "$f"\ndone',
        'import glob\nfor f in glob.glob("*.txt"):\n    with open(f) as fh:\n        print(len(fh.readlines()), f)',
        "bash", "python",
    ),
    # Python -> Go
    (
        'def contains(lst, item):\n    return item in lst',
        'func contains(lst []string, item string) bool {\n    for _, v := range lst {\n        if v == item {\n            return true\n        }\n    }\n    return false\n}',
        "python", "go",
    ),
    # Python -> TypeScript
    (
        'def filter_even(nums):\n    return [x for x in nums if x % 2 == 0]',
        'function filterEven(nums: number[]): number[] {\n    return nums.filter(x => x % 2 === 0);\n}',
        "python", "typescript",
    ),
    # C -> Rust
    (
        'void swap(int *a, int *b) {\n    int tmp = *a;\n    *a = *b;\n    *b = tmp;\n}',
        'fn swap(a: &mut i32, b: &mut i32) {\n    std::mem::swap(a, b);\n}',
        "c", "rust",
    ),
    # Java -> Kotlin
    (
        'public String greet(String name) {\n    if (name == null) {\n        return "Hello, World!";\n    }\n    return "Hello, " + name + "!";\n}',
        'fun greet(name: String?): String {\n    return "Hello, ${name ?: "World"}!"\n}',
        "java", "kotlin",
    ),
    # Python -> Java
    (
        'def reverse_string(s):\n    return s[::-1]',
        'public static String reverseString(String s) {\n    return new StringBuilder(s).reverse().toString();\n}',
        "python", "java",
    ),
    # C -> Go
    (
        'int strlen_custom(const char *s) {\n    int len = 0;\n    while (*s++) len++;\n    return len;\n}',
        'func strlenCustom(s string) int {\n    return len(s)\n}',
        "c", "go",
    ),
    # Rust -> Python
    (
        'fn fibonacci(n: u32) -> u64 {\n    match n {\n        0 => 0,\n        1 => 1,\n        _ => fibonacci(n - 1) + fibonacci(n - 2),\n    }\n}',
        'def fibonacci(n):\n    if n == 0:\n        return 0\n    if n == 1:\n        return 1\n    return fibonacci(n - 1) + fibonacci(n - 2)',
        "rust", "python",
    ),
    # Go -> Python
    (
        'func isPalindrome(s string) bool {\n    runes := []rune(s)\n    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {\n        if runes[i] != runes[j] {\n            return false\n        }\n    }\n    return true\n}',
        'def is_palindrome(s):\n    return s == s[::-1]',
        "go", "python",
    ),
    # JavaScript -> Rust
    (
        'function flatten(arr) {\n    return arr.reduce((acc, val) => \n        Array.isArray(val) ? acc.concat(flatten(val)) : acc.concat(val), []);\n}',
        'fn flatten(arr: &[serde_json::Value]) -> Vec<serde_json::Value> {\n    let mut result = Vec::new();\n    for val in arr {\n        match val {\n            serde_json::Value::Array(inner) => result.extend(flatten(inner)),\n            other => result.push(other.clone()),\n        }\n    }\n    result\n}',
        "javascript", "rust",
    ),
    # Python -> Bash
    (
        'import os\nfor f in os.listdir("."):\n    if f.endswith(".log"):\n        os.remove(f)',
        'for f in *.log; do\n    [ -f "$f" ] && rm "$f"\ndone',
        "python", "bash",
    ),
    # Python -> Dart
    (
        'class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n\n    def distance(self, other):\n        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5',
        'class Point {\n  final double x;\n  final double y;\n  Point(this.x, this.y);\n\n  double distance(Point other) {\n    return sqrt(pow(x - other.x, 2) + pow(y - other.y, 2));\n  }\n}',
        "python", "dart",
    ),
    # Lisp -> Python
    (
        '(defun square-list (lst)\n  (mapcar (lambda (x) (* x x)) lst))',
        'def square_list(lst):\n    return [x * x for x in lst]',
        "lisp", "python",
    ),
    # Python -> Lisp (ECL)
    (
        'def map_filter(lst, pred, func):\n    return [func(x) for x in lst if pred(x)]',
        '(defun map-filter (lst pred func)\n  (mapcar func (remove-if-not pred lst)))',
        "python", "lisp",
    ),
]


# ============================================================================
# EXPANDED COMPLETION TEMPLATES
# ============================================================================

EXPANDED_COMPLETION_TEMPLATES: List[Tuple[str, str, str]] = [
    (
        'def fibonacci(n):\n    if n <= 1:\n        return n\n    <GAP>',
        'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)',
        "python",
    ),
    (
        '#include <stdio.h>\n\nint main() {\n    <GAP>\n    return 0;\n}',
        '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
        "c",
    ),
    (
        'fn main() {\n    let nums = vec![1, 2, 3, 4, 5];\n    <GAP>\n    println!("{}", sum);\n}',
        'fn main() {\n    let nums = vec![1, 2, 3, 4, 5];\n    let sum: i32 = nums.iter().sum();\n    println!("{}", sum);\n}',
        "rust",
    ),
    (
        'class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, item):\n        <GAP>\n\n    def pop(self):\n        <GAP>',
        'class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, item):\n        self.items.append(item)\n\n    def pop(self):\n        if not self.items:\n            raise IndexError("pop from empty stack")\n        return self.items.pop()',
        "python",
    ),
    (
        'void bubbleSort(int arr[], int n) {\n    <GAP>\n}',
        'void bubbleSort(int arr[], int n) {\n    for (int i = 0; i < n - 1; i++) {\n        for (int j = 0; j < n - i - 1; j++) {\n            if (arr[j] > arr[j + 1]) {\n                int temp = arr[j];\n                arr[j] = arr[j + 1];\n                arr[j + 1] = temp;\n            }\n        }\n    }\n}',
        "c",
    ),
    (
        'class LinkedList {\n    constructor() {\n        this.head = null;\n    }\n\n    append(val) {\n        <GAP>\n    }\n}',
        'class LinkedList {\n    constructor() {\n        this.head = null;\n    }\n\n    append(val) {\n        const node = { val, next: null };\n        if (!this.head) {\n            this.head = node;\n            return;\n        }\n        let curr = this.head;\n        while (curr.next) curr = curr.next;\n        curr.next = node;\n    }\n}',
        "javascript",
    ),
    (
        'func binarySearch(arr []int, target int) int {\n    low, high := 0, len(arr)-1\n    <GAP>\n    return -1\n}',
        'func binarySearch(arr []int, target int) int {\n    low, high := 0, len(arr)-1\n    for low <= high {\n        mid := (low + high) / 2\n        if arr[mid] == target {\n            return mid\n        } else if arr[mid] < target {\n            low = mid + 1\n        } else {\n            high = mid - 1\n        }\n    }\n    return -1\n}',
        "go",
    ),
    (
        'impl Iterator for Counter {\n    type Item = u32;\n\n    fn next(&mut self) -> Option<Self::Item> {\n        <GAP>\n    }\n}',
        'impl Iterator for Counter {\n    type Item = u32;\n\n    fn next(&mut self) -> Option<Self::Item> {\n        if self.count < self.max {\n            self.count += 1;\n            Some(self.count)\n        } else {\n            None\n        }\n    }\n}',
        "rust",
    ),
    (
        'def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    <GAP>',
        'def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    result.extend(right[j:])\n    return result',
        "python",
    ),
    (
        'CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    <GAP>\n);',
        'CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    username VARCHAR(255) NOT NULL UNIQUE,\n    email VARCHAR(255) NOT NULL UNIQUE,\n    password_hash VARCHAR(255) NOT NULL,\n    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n);',
        "sql",
    ),
    (
        'FROM python:3.12-slim\nWORKDIR /app\n<GAP>\nCMD ["python", "app.py"]',
        'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8080\nUSER 1000\nCMD ["python", "app.py"]',
        "dockerfile",
    ),
    (
        '(defun flatten (lst)\n  <GAP>)',
        '(defun flatten (lst)\n  (cond\n    ((null lst) nil)\n    ((atom (car lst))\n     (cons (car lst) (flatten (cdr lst))))\n    (t (append (flatten (car lst))\n              (flatten (cdr lst))))))',
        "lisp",
    ),
]
