'use strict';
const common = require('../common.js');

const configs = {
  n: [1, 2, 4],
  size: [16, 32, 64, 128],  // Custom configurations
  depth: [16, 32, 64],  // Custom configurations
};

const options = {
  flags: ["--max-old-space-size=4096"]
};

// main and configs are required, options is optional.
const bench = common.createBenchmark(main, configs, options);

// Note that any code outside main will be run twice,
// in different processes, with different command line arguments.

class EmptyObject {

}

class Bar {
  constructor(number, depth) {
    this.anotherString = "just another string";
    let i;
    for(i=0; i < number; i++) {
      this[i] = number;
      this[number + i] = new EmptyObject();
    }
    if(depth > 0) {
      this.child = new Bar(number, depth - 1);
    }
  }
}

class Foo {
  constructor(number, depth) {
    this.simpleString = "simple string";
    this.complexString = `complex string number #${number}`;
    this.bar = new Bar(number, depth);
  }
}

function main(conf) {
  let i;
  let arrayOfObjects = [];
  const n = Number(conf.n);
  const size = Number(conf.size);
  const depth = Number(conf.depth);

  for(i=0; i < size; i++) {
    arrayOfObjects.push(new Foo(i, depth));
  }

  // Start the timer
  bench.start();

  for(i=0; i < n; i++) {
    process.enablePerfBasicProf();

    process.disablePerfBasicProf();
  }

  // End the timer, pass in the number of operations
  bench.end(n);
}
