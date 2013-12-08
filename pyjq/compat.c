#include <jq.h>
#include <jv.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <pyjq/vpool.h>

// Compatibility layer for jq
// Defines a type jq_compat which essentially emulates the loop of jq's main
// function. You can write to it and ask it to compile code, which may cause 
// it to write to buffers it maintains for error and output. These can then be
// read as strings.

typedef struct {
  jq_state *state;
  int had_error;
  struct jv_parser *parser;
  struct vpool error;
  struct vpool output;
} jq_compat;

// Appends string to the end of a vpool. Does not zero terminate the result
void vpool_append(struct vpool *pool, const char *s){
  vpool_insert(pool, VPOOL_TAIL, s, strlen(s));
}

// Return the contents of the vpool as a zero terminated string and resets
// it to 0.
char *vpool_read(struct vpool *pool){
  // Appends a 0 byte to the end of the vpool
  vpool_insert(pool, VPOOL_TAIL, "", 1);
  // This just resets the flags about where it is written, not the actual 
  // contents.
  vpool_wipe(pool);
  return vpool_get_buf(pool);
}

void jq_compat_err_cb(void *c, jv v){
  jq_compat *compat = (jq_compat*)c;
  compat->had_error = 1;
  vpool_append(&compat->error, jv_string_value(v));
  vpool_append(&compat->error, "\n");
}

jq_compat *jq_compat_new(){
  jq_compat *compat = malloc(sizeof(jq_compat));
  compat->state = jq_init();
  vpool_init(&compat->error, 1024, 0);  
  vpool_init(&compat->output, 1024, 0);  
  compat->had_error = 0;
  compat->parser = jv_parser_new(0);
  jq_set_error_cb(compat->state, jq_compat_err_cb, compat);
  return compat;
}

void jq_compat_del(jq_compat *compat){
  jq_teardown(&compat->state);
  vpool_final(&compat->error);
  vpool_final(&compat->output);
  jv_parser_free(compat->parser);
  free(compat);
}

void jq_compat_clear_error(jq_compat *compat){
  compat->had_error = 0;
  vpool_wipe(&compat->error);
}

int jq_compat_had_error(jq_compat *compat){
  return compat->had_error;
}

int jq_compat_compile(jq_compat *compat, char *program){
  return jq_compile(compat->state, program);
}

void jq_compat_write(jq_compat *compat, size_t n, char *data){
  jv_parser_set_buf(compat->parser, data, n, 0);
  jv value;
  while (jv_is_valid((value = jv_parser_next(compat->parser)))){
    jq_start(compat->state, value, 0);
    jv result;
    while (jv_is_valid(result = jq_next(compat->state))){
      jv result_s = jv_dump_string(result, 0);
      vpool_append(&compat->output, jv_string_value(result_s));
      vpool_append(&compat->output, "\n");
      jv_free(result_s);
      // don't need to jv_free result because _dump_string decreffed it 
    }
    jv_free(result);
  }
  if(jv_invalid_has_msg(jv_copy(value))) {
    jv msg = jv_invalid_get_msg(value);
    jq_compat_err_cb(compat, msg);
    jv_free(msg);
  } else {
    jv_free(value);
  }
}

const char *jq_compat_read_error(jq_compat *compat){
  return vpool_read(&compat->error);
}

const char *jq_compat_read_output(jq_compat *compat){
  return vpool_read(&compat->output);
}
