import java.io.*;
import java.net.URI;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.gradle.wrapper.*;

/** Use the SDK's official Wrapper for URL hashing, locking, verification and extraction. */
class PrepareGradle {
    public static void main(String[] args) throws Exception {
        String mode = args[0];
        File home = new File(args[1]);
        for (String line : Files.readAllLines(Path.of(args[2]))) {
            if (line.isBlank()) continue;
            String[] fields = line.split("\\t");
            String original = fields[0], mirror = fields[1], checksum = fields[2];
            WrapperConfiguration config = new WrapperConfiguration();
            config.setDistribution(URI.create(original));
            config.setDistributionSha256Sum(checksum);
            PathAssembler assembler = new PathAssembler(home);
            var local = assembler.getDistribution(config);
            File zip = local.getZipFile();
            File marker = new File(zip.getPath() + ".ok");
            File[] dirs = local.getDistributionDir().listFiles(f -> f.isDirectory() && f.getName().startsWith("gradle-"));
            boolean ready = marker.isFile() && dirs != null && dirs.length == 1
                && new File(dirs[0], "bin/gradle").isFile();
            if (mode.equals("check")) {
                System.out.println((ready ? "READY\t" : "MISSING\t") + original + "\t" + local.getDistributionDir());
                continue;
            }
            if (mode.equals("verify") && !ready) throw new IOException("Missing distribution: " + original);
            IDownload download = (source, destination) -> {
                if (!mode.equals("prepare")) throw new IOException("Verification must not download: " + source);
                if (!source.toString().equals(original)) throw new IOException("Unexpected distribution URL");
                System.out.println("Mirror download: " + mirror);
                // Called inside Install's official exclusive ZIP lock. No second archive store.
                Process process = new ProcessBuilder("/usr/bin/curl", "--fail", "--location", "--silent", "--show-error",
                    "--noproxy", "*", "--connect-timeout", "15", "--max-time", "900",
                    "--output", destination.toString(), mirror).inheritIO().start();
                Thread cleanup = new Thread(() -> { process.destroyForcibly(); destination.delete(); });
                Runtime.getRuntime().addShutdownHook(cleanup);
                try {
                    if (process.waitFor() != 0) throw new IOException("Mirror download failed: " + mirror);
                    MessageDigest digest = MessageDigest.getInstance("SHA-256");
                    try (InputStream input = new FileInputStream(destination)) {
                        byte[] buffer = new byte[65536]; int count;
                        while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
                    }
                    if (!HexFormat.of().formatHex(digest.digest()).equals(checksum))
                        throw new IOException("Official SHA-256 mismatch: " + mirror);
                } catch (Exception error) { destination.delete(); throw error; }
                finally { Runtime.getRuntime().removeShutdownHook(cleanup); }
            };
            File installed = new Install(new Logger(false), download, assembler).createDist(config);
            System.out.println("READY\t" + original + "\t" + installed);
            if (mode.equals("verify")) {
                ProcessBuilder pb = new ProcessBuilder(new File(installed, "bin/gradle").toString(), "--version");
                for (String key : List.of("GRADLE_OPTS", "JAVA_OPTS", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS")) pb.environment().remove(key);
                pb.environment().put("GRADLE_USER_HOME", home.toString());
                if (pb.inheritIO().start().waitFor() != 0) throw new IOException("Gradle startup failed");
            }
        }
    }
}
