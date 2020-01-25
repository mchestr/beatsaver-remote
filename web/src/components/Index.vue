<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <p>Visit <a href="https://bsaber.com">Beast Saber</a>, find a song, right click copy link address of
      the down arrow icon, paste it here.</p>

    <div>
      <input v-on:keyup.enter="sendLink" v-model="currentLink" placeholder="paste link here" aria-label="link">
    </div>
    <div>
      <button v-on:click="sendLink">Submit</button>
    </div>
    <ol>
      <li v-for="link in submittedLinks" v-bind:key="link.id"
          v-bind:class="{ submitted: link.state === 'submitted', complete: link.state === 'complete', error: link.state === 'error'}">
        {{ link.name || link.value }}
      </li>
    </ol>
  </div>
</template>

<script>
  export default {
    name: 'Index',
    data: function () {
      return {
        currentLink: '',
        submittedLinks: [],
      };
    },
    props: {
      msg: String
    },
    mounted: function () {
      this.$options.sockets.onmessage = this.onmessage;
    },
    destroyed: function () {
      delete this.$options.sockets.onmessage;
    },
    methods: {
      sendLink: function () {
        const id = Math.floor(Math.random() * 100000);
        const link = {
          value: this.currentLink,
          id: id,
          state: 'submitted',
        };

        this.submittedLinks.push(link);
        this.$socket.sendObj({type: 'link-submit', value: link.value, id: link.id});
        this.currentLink = '';
      },
      onmessage: function (msg) {
        const data = JSON.parse(msg.data);
        console.log(data);
        if (data.type === 'links') {
          this.submittedLinks = data.links || [];
        } else if (data.type === 'link-state') {
          this.submittedLinks.filter(link => link.id === data.id).map(link => {
            link.state = data.state;
          });
        } else if (data.type === 'link-submit') {
          this.submittedLinks.push(data);
        } else if (data.type === 'link-name') {
          this.submittedLinks.filter(link => link.id === data.id).map(link => {
            link.name = data.name;
          });
        }
      }
    },
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  h3 {
    margin: 40px 0 0;
  }

  ol {
    list-style-type: none;
    padding: 0;
    text-align: center;
    list-style-position: inside;
  }

  li {
    margin: 0 10px;
  }

  a {
    color: #42b983;
  }

  input {
    width: 50%;
  }

  button {
    margin-top: 1em;
    margin-bottom: 3em;
  }

  .submitted {
    color: dimgrey;
  }

  .complete {
    color: forestgreen;
  }

  .error {
    color: orangered;
  }

  .hidden {
    visibility: hidden;
  }

  ::-webkit-input-placeholder {
    text-align: center;
  }

  :-moz-placeholder { /* Firefox 18- */
    text-align: center;
  }

  ::-moz-placeholder { /* Firefox 19+ */
    text-align: center;
  }

  :-ms-input-placeholder {
    text-align: center;
  }
</style>
