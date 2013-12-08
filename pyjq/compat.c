#include <jq.h>
#include <jv.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define DEFAULT_BUFFER_LENGTH 1024

typedef struct {
  size_t capacity;
  size_t length;
  char *buffer;
} string_buffer;

string_buffer *jq_compat_buf_new(){
  string_buffer *buf = malloc(sizeof(string_buffer));
  buf->buffer = malloc(DEFAULT_BUFFER_LENGTH);
  buf->length = 0;
  buf->capacity = DEFAULT_BUFFER_LENGTH;
  return buf;
}

void jq_compat_buf_del(string_buffer *buf){
  free(buf->buffer);
  free(buf);
}

void jq_compat_buf_reset(string_buffer *buf){
  buf->length = 0;
}

void jq_compat_buf_ensure_capacity(string_buffer *buf, size_t n){
  if(n > buf->capacity){
    fflush(stdout);
    buf->buffer = realloc(buf->buffer, n);
    buf->capacity = n;
  }
}

void jq_compat_buf_ensure_extra_capacity(string_buffer *buf, size_t extra){
  jq_compat_buf_ensure_capacity(buf, extra + buf->length);
}

void jq_compat_buf_terminate(string_buffer *buf){
  jq_compat_buf_ensure_extra_capacity(buf, 1);
  buf->buffer[buf->length] = '\0';
  buf->length += 1; 
}

void jq_compat_buf_append(string_buffer *buf, const char *s){
  size_t l = strlen(s);
  if(!l){
    return;
  }
  jq_compat_buf_ensure_extra_capacity(buf, l);
  char *write_start = buf->buffer + buf->length;
  memcpy(write_start, s, l);
  buf->length += l;
}

void jq_compat_buf_set(string_buffer *buf, const char *s){
  jq_compat_buf_reset(buf);
  jq_compat_buf_append(buf, s);
}

typedef struct {
  jq_state *state;
  struct jv_parser *parser;
  string_buffer *error;
  string_buffer *output;
} jq_compat;

void jq_compat_err_cb(void *c, jv v){
  jq_compat *compat = (jq_compat*)c;
  jq_compat_buf_append(compat->error, jv_string_value(v));
  jq_compat_buf_append(compat->error, "\n");
}

jq_compat *jq_compat_new(){
  jq_compat *compat = malloc(sizeof(jq_compat));
  compat->state = jq_init();
  compat->error = jq_compat_buf_new();
  compat->parser = jv_parser_new(0);
  compat->output = jq_compat_buf_new();
  jq_set_error_cb(compat->state, jq_compat_err_cb, compat);
  return compat;
}

void jq_compat_del(jq_compat *compat){
  jq_teardown(&compat->state);
  jq_compat_buf_del(compat->error);
  jq_compat_buf_del(compat->output);
  jv_parser_free(compat->parser);
  free(compat);
}

int jq_compat_compile(jq_compat *compat, char *program){
  jq_compat_buf_reset(compat->error);
  return jq_compile(compat->state, program);
}

char *jq_compat_current_error(jq_compat *compat){
  if(compat->error->length){
    return compat->error->buffer;
  } else {
    return NULL;
  }
}

void jq_compat_write(jq_compat *compat, size_t n, char *data){
  jv_parser_set_buf(compat->parser, data, n, 0);
  jv value;
  while (jv_is_valid((value = jv_parser_next(compat->parser)))){
    jq_start(compat->state, value, 0);
    jv result;
    while (jv_is_valid(result = jq_next(compat->state))){
      jv result_s = jv_dump_string(result, 0);
      jq_compat_buf_append(compat->output, jv_string_value(result_s));
      jq_compat_buf_append(compat->output, "\n");
      jv_free(result_s);
      jv_free(result);
    }
  }
}

char *jq_compat_read(jq_compat *compat){
  if(!compat->output->length){
    return NULL;
  }
  jq_compat_buf_terminate(compat->output);
  jq_compat_buf_reset(compat->output);
  return compat->output->buffer;
}
