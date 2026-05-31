package com.rhysticlibrary.boot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point that boots the Rhystic Library API. */
@SpringBootApplication
public class RhysticLibraryApplication {

  /**
   * Starts the Spring application context.
   *
   * @param args command-line arguments
   */
  public static void main(String[] args) {
    SpringApplication.run(RhysticLibraryApplication.class, args);
  }
}
