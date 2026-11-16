// STAGE1_alloy/a6RandomModels.java -- pipeline copy (loosepin, 2026-11-09) of
// STAGE1_alloy/models/proposed_twophase/dedup_audit/a6RandomModels.java (dedup-audit-s15), code unchanged.
// Used by alloy_solver_order.py when alloy.solver_order.mode = "random"; compiled on demand (javac -cp alloy6.jar:. a6RandomModels.java).
// PROBE (dedup audit 2026-11-09): a6CountModels with a seeded, randomized SAT4J.
// javac -cp ../../../STAGE1_alloy/alloy6.jar -d . a6RandomModels.java
// java  -cp alloy6.jar:<dir of this class> a6RandomModels <model.als> <out_dir> <limit> <seed> [randomWalkProb=0.05]
// Same translation, same formula, same blocking-clause enumeration as a6CountModels (sol.next()):
// only the SAT search order changes (random phase + random-walk decisions), so every instance is
// still a model instance and a run that ends below the limit is still exhaustive.
import edu.mit.csail.sdg.alloy4.A4Reporter;
import edu.mit.csail.sdg.ast.Command;
import edu.mit.csail.sdg.ast.Func;
import edu.mit.csail.sdg.ast.Module;
import edu.mit.csail.sdg.parser.CompUtil;
import edu.mit.csail.sdg.translator.A4Options;
import edu.mit.csail.sdg.translator.A4Solution;
import edu.mit.csail.sdg.translator.TranslateAlloyToKodkod;
import kodkod.engine.satlab.SATFactory;
import kodkod.engine.satlab.SATSolver;
import org.sat4j.minisat.SolverFactory;
import org.sat4j.minisat.core.Solver;
import org.sat4j.minisat.orders.RandomLiteralSelectionStrategy;
import org.sat4j.minisat.orders.RandomWalkDecorator;
import org.sat4j.minisat.orders.VarOrderHeap;
import java.lang.reflect.Field;
import java.nio.file.*;
import java.util.Collections;
import java.util.Random;

public class a6RandomModels {
  static long SEED; static double P;
  public static class RandSAT4J extends SATFactory {
    public String id() { return "sat4j.random"; }
    public String type() { return "jni"; }
    public boolean incremental() { return true; }
    public SATSolver createSolver() {
      try {
        Solver s = SolverFactory.newMiniLearningHeap();
        RandomLiteralSelectionStrategy.RAND.setSeed(SEED);
        VarOrderHeap heap = new VarOrderHeap(new RandomLiteralSelectionStrategy());
        RandomWalkDecorator rw = new RandomWalkDecorator(heap, P);
        Field f = RandomWalkDecorator.class.getDeclaredField("rand");
        f.setAccessible(true); f.set(rw, new Random(SEED ^ 0x5DEECE66DL));
        s.setOrder(rw);
        return new kodkod.solvers.SAT4J(s);
      } catch (Exception e) { throw new RuntimeException(e); }
    }
  }
  public static void main(String[] a) throws Exception {
    Path out = Paths.get(a[1]); long limit = Long.parseLong(a[2]);
    SEED = Long.parseLong(a[3]); P = a.length > 4 ? Double.parseDouble(a[4]) : 0.05;
    A4Reporter rep = new A4Reporter();
    Module world = CompUtil.parseEverything_fromFile(rep, null, a[0]);
    Command cmd = world.getAllCommands().get(0);
    A4Options opt = new A4Options();
    opt.solver = new RandSAT4J();
    opt.symmetry = 80;
    long t0 = System.currentTimeMillis();
    A4Solution sol = TranslateAlloyToKodkod.execute_command(rep, world.getAllSigs(), cmd, opt);
    Files.createDirectories(out);
    long n = 0;
    while (sol.satisfiable() && n < limit) {
      n++;
      sol.writeXML(out.resolve(String.format("inst-%06d.xml", n)).toString(), Collections.<Func>emptyList());
      Files.writeString(out.resolve(String.format("inst-%06d.txt", n)), sol.toString());
      sol = sol.next();
    }
    System.out.println("Total models: " + n + " seed=" + SEED + " p=" + P + " secs=" + (System.currentTimeMillis() - t0) / 1000.0);
  }
}
