#include "pyjq/compat.c"

void jqcw(jq_compat *jqc, char *s){
}

void test_field_access(){
    jq_compat *jqc = jq_compat_new();
    jq_compat_compile(jqc, ".foo");
    char *line = "{\"foo\" :1}";
    int ll = strlen(line);
    int n = 10;
    for(int i = 0; i < n; i++){
        jq_compat_write(jqc, ll, line);
    }

    const char *result = jq_compat_read_output(jqc);
    assert(result != NULL);
    // n '1's and n '\n's
    assert(strlen(result) == n * 2);

    jq_compat_del(jqc); 
}

void test_del_before_read(){
    jq_compat *jqc = jq_compat_new();
    jq_compat_compile(jqc, ".foo");
    char *line = "{\"foo\" :1}";
    int ll = strlen(line);
    int n = 10;
    for(int i = 0; i < n; i++){
        jq_compat_write(jqc, ll, line);
    }

    jq_compat_del(jqc); 
}

void test_pass_data_through(){
    jq_compat *jqc = jq_compat_new();
    jq_compat_compile(jqc, ".");
    char *line = "1";
    int ll = strlen(line);
    for(int i = 0; i < 5; i++){
        int n = 10;
        for(int i = 0; i < n; i++){
            jq_compat_write(jqc, ll, line);
        }

        const char *result = jq_compat_read_output(jqc);
        assert(result != NULL);
        // n '1's and n '\n's
        assert(strlen(result) == n * 2);
    }

    jq_compat_del(jqc); 
}

void test_memory_corruption(){
  // This replicates a case which caused memory corruption with a double free bug
  jq_compat *jqc = jq_compat_new();
  jq_compat_clear_error(jqc);
  jq_compat_compile(jqc, ".foo");
  jq_compat_write(jqc, 10, "{\"foo\": 0}");
  jq_compat_write(jqc, 10, "{\"foo\": 1}");
  jq_compat_write(jqc, 10, "{\"foo\": 2}");
  jq_compat_write(jqc, 10, "{\"foo\": 3}");
  jq_compat_write(jqc, 10, "{\"foo\": 4}");
  jq_compat_write(jqc, 10, "{\"foo\": 5}");
  jq_compat_write(jqc, 10, "{\"foo\": 6}");
  jq_compat_write(jqc, 10, "{\"foo\": 7}");
  jq_compat_write(jqc, 10, "{\"foo\": 8}");
  jq_compat_write(jqc, 10, "{\"foo\": 9}");
  jq_compat_write(jqc, 14, "{\"foo\": \"foo\"}");
  jq_compat_write(jqc, 14, "{\"foo\": \"bar\"}");
}


int main(){
  test_memory_corruption();
  test_field_access();
  test_del_before_read();
  test_pass_data_through();
}
