import React, { useEffect, useRef, useState } from "react";
import { Camera, ChevronRight, Crosshair, Gauge } from "lucide-react";
import { FilesetResolver, PoseLandmarker } from "@mediapipe/tasks-vision";

function Camera67({ onReward }) {
  const videoRef = useRef(null),
    streamRef = useRef(),
    landmarkerRef = useRef(),
    frameRef = useRef(),
    phaseRef = useRef(0),
    scoreRef = useRef(0),
    startRef = useRef();
  const [status, setStatus] = useState("intro"),
    [score, setScore] = useState(0),
    [remaining, setRemaining] = useState(20),
    [error, setError] = useState("");
  useEffect(
    () => () => {
      cancelAnimationFrame(frameRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      landmarkerRef.current?.close();
    },
    [],
  );
  const start = async () => {
    try {
      setStatus("loading");
      setError("");
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 960, height: 540 },
        audio: false,
      });
      videoRef.current.srcObject = streamRef.current;
      await videoRef.current.play();
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm",
      );
      landmarkerRef.current = await PoseLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath:
            "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        numPoses: 1,
      });
      scoreRef.current = 0;
      phaseRef.current = 0;
      startRef.current = performance.now();
      setScore(0);
      setRemaining(20);
      setStatus("playing");
      frameRef.current = requestAnimationFrame(track);
    } catch (e) {
      setStatus("intro");
      setError(
        "Camera or pose tracking could not start. Allow camera access and check your connection, then retry.",
      );
    }
  };
  const track = async () => {
    const elapsed = performance.now() - startRef.current;
    if (elapsed >= 20000) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      setRemaining(0);
      setStatus("done");
      return;
    }
    setRemaining(Math.max(0, 20 - elapsed / 1000));
    if (videoRef.current?.readyState >= 2) {
      const result = landmarkerRef.current.detectForVideo(
          videoRef.current,
          performance.now(),
        ),
        pose = result.landmarks?.[0];
      if (pose) {
        const delta = pose[15].y - pose[16].y;
        const next = delta > 0.085 ? 1 : delta < -0.085 ? -1 : 0;
        if (next && phaseRef.current && next !== phaseRef.current) {
          scoreRef.current += 1;
          setScore(scoreRef.current);
        }
        if (next) phaseRef.current = next;
      }
    }
    frameRef.current = requestAnimationFrame(track);
  };
  return (
    <section className="camera-game">
      <div className="game-hud">
        <span>TIME {remaining.toFixed(1)}s</span>
        <b>{score} PUMPS</b>
      </div>
      <div className="camera-stage">
        <video ref={videoRef} muted playsInline />
        <div className="camera-guide">
          <i />
          <span>
            Both wrists visible · alternating separation threshold 8.5%
          </span>
        </div>
        {status === "intro" && (
          <div className="camera-overlay">
            <Camera />
            <h3>67 Camera Sprint</h3>
            <p>
              Face the camera and alternate your hands up and down. Full-range
              wrist crossings count; small camera jitter does not.
            </p>
            <button onClick={start}>ENABLE CAMERA & START</button>
            <small>
              Video is processed on this device and is not recorded or uploaded.
            </small>
            {error && <em>{error}</em>}
          </div>
        )}
        {status === "loading" && (
          <div className="camera-overlay">
            <Gauge />
            <h3>Loading pose tracker…</h3>
          </div>
        )}
        {status === "done" && (
          <div className="camera-overlay">
            <strong>{score}</strong>
            <h3>67 pumps completed</h3>
            <button
              onClick={() =>
                onReward(
                  Math.min(1500, 300 + score * 60),
                  `${score} camera-tracked pumps`,
                )
              }
            >
              CLAIM ${Math.min(1500, 300 + score * 60)} <ChevronRight />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function RapidTargets({ onReward }) {
  const [state, setState] = useState("intro"),
    [index, setIndex] = useState(0),
    [hits, setHits] = useState(0),
    [target, setTarget] = useState({ x: 50, y: 50, id: 0, alive: true });
  const timer = useRef(),
    hitRef = useRef(0);
  useEffect(() => () => clearInterval(timer.current), []);
  const start = () => {
    setState("playing");
    setIndex(1);
    setHits(0);
    hitRef.current = 0;
    setTarget({
      x: 8 + Math.random() * 84,
      y: 12 + Math.random() * 76,
      id: 1,
      alive: true,
    });
    let n = 1;
    timer.current = setInterval(() => {
      n += 1;
      if (n > 30) {
        clearInterval(timer.current);
        setState("done");
        return;
      }
      setIndex(n);
      setTarget({
        x: 8 + Math.random() * 84,
        y: 12 + Math.random() * 76,
        id: n,
        alive: true,
      });
    }, 670);
  };
  const hit = () => {
    if (!target.alive) return;
    hitRef.current += 1;
    setHits(hitRef.current);
    setTarget((t) => ({ ...t, alive: false }));
  };
  return (
    <section className="game-stage">
      <div className="game-hud">
        <span>TARGET {index} / 30</span>
        <b>
          {hits} HITS · {index ? ((hits / index) * 100).toFixed(0) : 0}%
        </b>
      </div>
      <div className="aim-field rapid">
        {state === "intro" && (
          <div className="game-intro">
            <Crosshair />
            <h3>Rapid Target Grid</h3>
            <p>
              30 targets. One appears every 0.67 seconds and disappears whether
              you hit it or not.
            </p>
            <button onClick={start}>START 20.1-SECOND RUN</button>
          </div>
        )}
        {state === "playing" && target.alive && (
          <button
            key={target.id}
            aria-label="target"
            onClick={hit}
            style={{ left: `${target.x}%`, top: `${target.y}%` }}
          >
            <i />
          </button>
        )}
        {state === "done" && (
          <div className="game-intro">
            <strong>{hits} / 30</strong>
            <h3>targets hit</h3>
            <button
              onClick={() =>
                onReward(300 + hits * 40, `${hits}/30 timed targets`)
              }
            >
              CLAIM ${300 + hits * 40}
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function ReactionTrials({ onReward }) {
  const [phase, setPhase] = useState("intro"),
    [trial, setTrial] = useState(1),
    [results, setResults] = useState([]),
    [last, setLast] = useState(),
    timer = useRef(),
    startRef = useRef();
  useEffect(() => () => clearTimeout(timer.current), []);
  const startTrial = () => {
    setLast();
    setPhase("wait");
    timer.current = setTimeout(
      () => {
        startRef.current = performance.now();
        setPhase("go");
      },
      1400 + Math.random() * 2600,
    );
  };
  const react = () => {
    if (phase === "wait") {
      clearTimeout(timer.current);
      setPhase("early");
    } else if (phase === "go") {
      const ms = Math.round(performance.now() - startRef.current),
        next = [...results, ms];
      setResults(next);
      setLast(ms);
      setPhase("review");
    }
  };
  const next = () => {
    if (results.length >= 5) setPhase("done");
    else {
      setTrial(results.length + 1);
      startTrial();
    }
  };
  const best = results.length ? Math.min(...results) : 0,
    reward = Math.max(300, Math.min(1500, 2400 - best * 4));
  if (phase === "intro")
    return (
      <section className="campaign-stage reaction-intro">
        <Gauge />
        <h2>Five-Trial Reaction Gate</h2>
        <p>
          Complete five valid trials. Every reaction time is shown; your fastest
          result determines the reward.
        </p>
        <button className="campaign-primary" onClick={startTrial}>
          START TRIAL 1
        </button>
      </section>
    );
  if (phase === "review")
    return (
      <section className="campaign-stage trial-review">
        <span>TRIAL {results.length} / 5</span>
        <strong>{last} ms</strong>
        <div>
          {results.map((r, i) => (
            <b className={r === Math.min(...results) ? "best" : ""} key={i}>
              #{i + 1} {r} ms
            </b>
          ))}
        </div>
        <button onClick={next}>
          {results.length === 5
            ? "VIEW FINAL RESULT"
            : `START TRIAL ${results.length + 1}`}
        </button>
      </section>
    );
  if (phase === "done")
    return (
      <section className="campaign-stage trial-review">
        <span>FASTEST OF FIVE</span>
        <strong>{best} ms</strong>
        <div>
          {results.map((r, i) => (
            <b className={r === best ? "best" : ""} key={i}>
              #{i + 1} {r} ms
            </b>
          ))}
        </div>
        <button onClick={() => onReward(reward, `${best} ms best of five`)}>
          CLAIM ${Math.round(reward)}
        </button>
      </section>
    );
  return (
    <section className={`reaction-field ${phase}`} onClick={react}>
      <Gauge />
      <strong>
        {phase === "wait"
          ? "WAIT FOR GREEN"
          : phase === "go"
            ? "CLICK NOW"
            : "TOO EARLY"}
      </strong>
      <span>Trial {trial} / 5</span>
      {phase === "early" && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            startTrial();
          }}
        >
          RETRY TRIAL
        </button>
      )}
    </section>
  );
}

export default function ArcadeGames({ onReward }) {
  const [game, setGame] = useState();
  if (game === "67") return <Camera67 onReward={onReward} />;
  if (game === "aim") return <RapidTargets onReward={onReward} />;
  if (game === "reaction") return <ReactionTrials onReward={onReward} />;
  return (
    <section className="campaign-stage">
      <div className="stage-kicker">
        <Gauge /> EARN VIRTUAL CAPITAL
      </div>
      <h2>Choose one arcade trial</h2>
      <p>
        One game per market day. Skill affects your virtual investing budget.
      </p>
      <div className="game-choices">
        <button onClick={() => setGame("67")}>
          <Camera />
          <b>67 Camera Sprint</b>
          <span>
            20 seconds of real alternating hand pumps tracked by your webcam.
          </span>
        </button>
        <button onClick={() => setGame("aim")}>
          <Crosshair />
          <b>Rapid Target Grid</b>
          <span>
            30 targets appear for 0.67 seconds each. Missed targets disappear.
          </span>
        </button>
        <button onClick={() => setGame("reaction")}>
          <Gauge />
          <b>Reaction Gate</b>
          <span>
            Five measured trials. Your fastest valid time sets the reward.
          </span>
        </button>
      </div>
    </section>
  );
}
