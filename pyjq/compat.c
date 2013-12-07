#include <jq.h>
#include <jv.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

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

void jq_compat_buf_ensure_size(string_buffer *buf, size_t n){
  if(n > buf->capacity){
    buf->buffer = realloc(buf->buffer, n);
  }
}

void jq_compat_buf_ensure_extra_capacity(string_buffer *buf, size_t extra){
  jq_compat_buf_ensure_size(buf, extra + buf->length);
}

void jq_compat_buf_append(string_buffer *buf, const char *s){
  if(buf->length > 0){
    buf->buffer[buf->length-1] = '\n';
  }
  size_t l = strlen(s);
  jq_compat_buf_ensure_extra_capacity(buf, l + 1);
  char *write_start = buf->buffer + buf->length;
  memcpy(write_start, s, l);
  buf->length += (l + 1);
  buf->buffer[buf->length - 1] = '\0';
}

void jq_compat_buf_set(string_buffer *buf, const char *s){
  jq_compat_buf_reset(buf);
  jq_compat_buf_append(buf, s);
}

typedef struct {
  jq_state *state;
  string_buffer *error;
  string_buffer *input;
  string_buffer *output;
} jq_compat;

void jq_compat_err_cb(void *c, jv v){
  jq_compat *compat = (jq_compat*)c;
  jq_compat_buf_append(compat->error, jv_string_value(v));
}

jq_compat *jq_compat_new(){
  jq_compat *compat = malloc(sizeof(jq_compat));
  compat->state = jq_init();
  compat->error = jq_compat_buf_new();
  compat->input = jq_compat_buf_new();
  compat->output = jq_compat_buf_new();
  jq_set_error_cb(compat->state, jq_compat_err_cb, compat);
  return compat;
}

void jq_compat_del(jq_compat *x){
  jq_teardown(&x->state);
  jq_compat_buf_del(x->error);
  jq_compat_buf_del(x->input);
  jq_compat_buf_del(x->output);
  free(x);
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

void jq_compat_stage_data(jq_compat *compat, char *data){
  jq_compat_buf_append(compat->input, data);
}

void jq_compat_process_input(jq_compat *compat){
  if(!compat->input->length){
    return;
  }
  struct jv_parser* parser = jv_parser_new(0);
  jv_parser_set_buf(parser, compat->input->buffer, compat->input->length, 0);

  jv value;
  while (1){
    value = jv_parser_next(parser);
    if(!jv_is_valid(value)){
      break;
    }
    jq_start(compat->state, value, 0);
  }
  jv_parser_free(parser);
  jq_compat_buf_reset(compat->input);
}

char *jq_compat_value_next(jq_compat *compat){
  jv val = jq_next(compat->state);
  if(!jv_is_valid(val)){
    return NULL;
  }
  jv vals = jv_dump_string(val, 0);
  jq_compat_buf_set(compat->output, jv_string_value(vals));
  jv_free(val);
  jv_free(vals);
  return compat->output->buffer;
}
